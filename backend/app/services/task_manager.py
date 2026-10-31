"""
Background task manager for asynchronous lecture processing.
Coordinates audio extraction, speech recognition, summarization, topic extraction, and question generation.
Updates database progress status dynamically.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from backend.app.database.connection import SessionLocal
from backend.app.models.db_models import Lecture, Quiz
from backend.app.services.audio_service import extract_audio_from_media, get_media_duration_seconds
from backend.app.services.transcription_service import transcribe_audio_file
from backend.app.services.summarization_service import generate_lecture_summaries
from backend.app.services.topic_service import extract_lecture_topics
from backend.app.services.quiz_service import generate_mcqs_from_text

logger = logging.getLogger(__name__)


def process_lecture_pipeline(lecture_id: int, file_path_str: str, language_opt: str = "auto"):
    """
    Executes the multi-stage AI pipeline in a background task:
    1. Extract/normalize audio to 16kHz WAV
    2. Transcribe speech using Whisper
    3. Generate summaries, key concepts, bullet points, and study notes
    4. Extract key topics and terminology
    5. Pre-generate default practice quiz questions
    6. Mark as completed
    """
    db = SessionLocal()
    file_path = Path(file_path_str)

    try:
        lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
        if not lecture:
            logger.error("Lecture %d not found in database for processing.", lecture_id)
            return

        # 1. Start Audio Extraction
        lecture.status = "transcribing"
        lecture.progress_percent = 15
        lecture.status_message = "Extracting audio and preparing speech recognition..."
        db.commit()

        # Target temporary WAV file
        wav_path = file_path.parent / f"{file_path.stem}_16k.wav"
        ext = file_path.suffix.lower()

        if ext == ".wav":
            # Already wav, use directly or re-sample
            extract_success, err = extract_audio_from_media(file_path, wav_path)
            audio_target = wav_path if extract_success else file_path
        elif ext in {".mp3", ".m4a", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            extract_success, err = extract_audio_from_media(file_path, wav_path)
            if not extract_success:
                raise RuntimeError(f"Audio extraction failed: {err}")
            audio_target = wav_path
        else:
            raise ValueError(f"Unsupported media file format: {ext}")

        # Measure duration if possible
        duration = get_media_duration_seconds(audio_target)
        if duration > 0:
            lecture.duration_seconds = duration
            db.commit()

        # 2. Transcribe Speech
        lecture.progress_percent = 35
        lecture.status_message = "Running Whisper speech recognition..."
        db.commit()

        trans_res = transcribe_audio_file(audio_path=audio_target, language=language_opt)
        transcript_text = trans_res.get("transcript_text", "")
        segments = trans_res.get("segments", [])
        detected_lang = trans_res.get("detected_language", "en")
        actual_duration = trans_res.get("duration_seconds", duration)

        lecture.transcript_text = transcript_text
        lecture.transcript_segments_json = json.dumps(segments)
        lecture.detected_language = detected_lang
        if actual_duration > 0:
            lecture.duration_seconds = actual_duration

        # 3. Summarization
        lecture.status = "summarizing"
        lecture.progress_percent = 65
        lecture.status_message = "Generating summaries, key concepts, and structured notes..."
        db.commit()

        summary_res = generate_lecture_summaries(transcript_text)
        lecture.short_summary = summary_res["short_summary"]
        lecture.detailed_summary = summary_res["detailed_summary"]
        lecture.bullet_notes = summary_res["bullet_notes"]
        lecture.study_notes_json = json.dumps(summary_res["study_notes"])

        # 4. Topic Extraction
        topics_res = extract_lecture_topics(transcript_text)
        lecture.topics_json = json.dumps(topics_res)

        # 5. Generate Default Practice Quiz
        lecture.status = "generating_questions"
        lecture.progress_percent = 85
        lecture.status_message = "Synthesizing practice quiz questions from lecture concepts..."
        db.commit()

        mcqs = generate_mcqs_from_text(
            transcript_text=transcript_text,
            summary_text=lecture.short_summary,
            num_questions=5,
            difficulty="Medium"
        )

        quiz = Quiz(
            lecture_id=lecture.id,
            question_count=len(mcqs),
            difficulty_level="Medium",
            questions_json=json.dumps(mcqs)
        )
        db.add(quiz)

        # 6. Mark Completed
        lecture.status = "completed"
        lecture.progress_percent = 100
        lecture.status_message = "Processing complete! Notes, summary, and quiz are ready."
        lecture.updated_at = datetime.utcnow()
        db.commit()

        logger.info("Successfully completed AI processing pipeline for lecture %d (%s)", lecture_id, lecture.title)

        # Cleanup temporary wav file if different from original
        if wav_path.exists() and wav_path != file_path:
            try:
                os.remove(wav_path)
            except Exception:
                pass

    except Exception as e:
        logger.exception("Background processing error for lecture %d: %s", lecture_id, e)
        db.rollback()
        lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
        if lecture:
            lecture.status = "failed"
            lecture.progress_percent = 0
            lecture.status_message = "AI Processing encountered an error."
            lecture.error_message = str(e)
            db.commit()
    finally:
        db.close()
