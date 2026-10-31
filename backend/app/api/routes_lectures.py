"""
Lecture management and content retrieval API routes.
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from backend.app.config import (
    UPLOADS_DIR,
    MAX_UPLOAD_SIZE_MB,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
)
from backend.app.database.connection import get_db
from backend.app.models.db_models import Lecture
from backend.app.schemas.lecture_schemas import (
    LectureUploadResponse,
    LectureStatusResponse,
    LectureTranscriptResponse,
    LectureSummaryResponse,
    LectureNotesResponse,
    TranscriptSegment,
    StudyNotes,
    TopicExtractionResult,
)
from backend.app.services.task_manager import process_lecture_pipeline

router = APIRouter(prefix="/lectures", tags=["Lectures"])


@router.post("/upload", response_model=LectureUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_lecture_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    language: Optional[str] = Form("auto"),
    db: Session = Depends(get_db)
):
    """
    Upload a lecture video or audio file for speech recognition and summarization.
    Validates file format, size, prevents path traversal, and triggers AI processing asynchronously.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    original_filename = Path(file.filename).name # prevents path traversal
    file_ext = Path(original_filename).suffix.lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{file_ext}'. Allowed formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Generate a unique stored filename
    unique_token = uuid.uuid4().hex[:10]
    stored_filename = f"{unique_token}_{original_filename}"
    saved_path = UPLOADS_DIR / stored_filename

    # Stream write to disk while verifying size limit
    bytes_written = 0
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    try:
        with open(saved_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024):  # 1MB buffer
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    saved_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {MAX_UPLOAD_SIZE_MB}MB size limit."
                    )
                f_out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    file_size_mb = round(bytes_written / (1024 * 1024), 2)
    media_category = "video" if file_ext in SUPPORTED_VIDEO_EXTENSIONS else "audio"
    lecture_title = title.strip() if (title and title.strip()) else Path(original_filename).stem.replace("_", " ").title()

    # Create Lecture database record
    lecture = Lecture(
        title=lecture_title,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=media_category,
        file_size_mb=file_size_mb,
        status="uploaded",
        progress_percent=5,
        status_message="Upload received. Queued for AI transcription.",
        detected_language=language if language != "auto" else "en"
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    # Schedule background AI processing
    background_tasks.add_task(
        process_lecture_pipeline,
        lecture_id=lecture.id,
        file_path_str=str(saved_path),
        language_opt=language or "auto"
    )

    return LectureUploadResponse(
        id=lecture.id,
        title=lecture.title,
        original_filename=lecture.original_filename,
        file_type=lecture.file_type,
        file_size_mb=lecture.file_size_mb,
        status=lecture.status,
        message="File uploaded successfully. Background processing started."
    )


@router.get("/{lecture_id}/status", response_model=LectureStatusResponse)
def get_lecture_status(lecture_id: int, db: Session = Depends(get_db)):
    """Check processing status, percentage completion, and diagnostic messages."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    return LectureStatusResponse(
        id=lecture.id,
        title=lecture.title,
        status=lecture.status,
        progress_percent=lecture.progress_percent,
        status_message=lecture.status_message,
        error_message=lecture.error_message,
        duration_seconds=lecture.duration_seconds,
        detected_language=lecture.detected_language,
        updated_at=lecture.updated_at
    )


@router.get("/{lecture_id}/transcript", response_model=LectureTranscriptResponse)
def get_lecture_transcript(lecture_id: int, db: Session = Depends(get_db)):
    """Retrieve full transcript and timestamped segments."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    if lecture.status in ("uploaded", "transcribing"):
        raise HTTPException(
            status_code=425,
            detail="Transcription is still processing. Please check /status."
        )

    try:
        segments_raw = json.loads(lecture.transcript_segments_json or "[]")
        segments = [TranscriptSegment(**seg) for seg in segments_raw]
    except Exception:
        segments = []

    return LectureTranscriptResponse(
        lecture_id=lecture.id,
        title=lecture.title,
        detected_language=lecture.detected_language,
        duration_seconds=lecture.duration_seconds,
        transcript_text=lecture.transcript_text,
        segments=segments
    )


@router.get("/{lecture_id}/summary", response_model=LectureSummaryResponse)
def get_lecture_summary(lecture_id: int, db: Session = Depends(get_db)):
    """Retrieve executive summary, detailed summary, bullet points, and extracted topics."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    if lecture.status in ("uploaded", "transcribing", "summarizing"):
        raise HTTPException(
            status_code=425,
            detail="Summary is still being generated. Please check /status."
        )

    try:
        topics_dict = json.loads(lecture.topics_json or "{}")
        topics = TopicExtractionResult(**topics_dict)
    except Exception:
        topics = TopicExtractionResult()

    return LectureSummaryResponse(
        lecture_id=lecture.id,
        title=lecture.title,
        short_summary=lecture.short_summary or "No summary available.",
        detailed_summary=lecture.detailed_summary or "No detailed summary available.",
        bullet_notes=lecture.bullet_notes or "• No notes available.",
        topics=topics
    )


@router.get("/{lecture_id}/notes", response_model=LectureNotesResponse)
def get_lecture_notes(lecture_id: int, db: Session = Depends(get_db)):
    """Retrieve structured study guide: definitions, key takeaways, and exam prep tips."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    try:
        notes_dict = json.loads(lecture.study_notes_json or "{}")
        study_notes = StudyNotes(**notes_dict)
    except Exception:
        study_notes = StudyNotes()

    return LectureNotesResponse(
        lecture_id=lecture.id,
        title=lecture.title,
        study_notes=study_notes,
        bullet_notes=lecture.bullet_notes or ""
    )


@router.delete("/{lecture_id}", status_code=status.HTTP_200_OK)
def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    """Delete lecture record, stored media file, and associated quizzes."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    # Remove stored media file
    if lecture.stored_filename:
        file_path = UPLOADS_DIR / lecture.stored_filename
        file_path.unlink(missing_ok=True)

    db.delete(lecture)
    db.commit()

    return {"message": f"Lecture {lecture_id} ('{lecture.title}') deleted successfully."}
