"""
Speech recognition module for LectureAI using faster-whisper.
Converts lecture audio to timestamped text with automatic or manual language detection.
"""

import logging
import functools
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from config import (
    DEFAULT_WHISPER_MODEL,
    DEFAULT_DEVICE,
    DEFAULT_COMPUTE_TYPE,
    MODELS_CACHE_DIR,
)

logger = logging.getLogger(__name__)

# Global cache for loaded Whisper model to prevent reloading across Streamlit interactions
_LOADED_WHISPER_MODELS = {}


def get_whisper_model(
    model_size: str = DEFAULT_WHISPER_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
):
    """
    Load or retrieve a cached faster-whisper WhisperModel instance.
    """
    from faster_whisper import WhisperModel

    cache_key = f"{model_size}_{device}_{compute_type}"
    if cache_key in _LOADED_WHISPER_MODELS:
        return _LOADED_WHISPER_MODELS[cache_key]

    logger.info(
        "Loading faster-whisper model '%s' (device=%s, compute_type=%s)...",
        model_size,
        device,
        compute_type,
    )

    try:
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(MODELS_CACHE_DIR),
        )
        _LOADED_WHISPER_MODELS[cache_key] = model
        return model
    except Exception as e:
        logger.warning(
            "Failed to load model '%s' with compute_type '%s': %s. Retrying with 'int8' on CPU.",
            model_size,
            compute_type,
            e,
        )
        # Fallback to safe int8 on CPU
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(MODELS_CACHE_DIR),
        )
        _LOADED_WHISPER_MODELS[f"{model_size}_cpu_int8"] = model
        return model


def transcribe_audio(
    audio_path: Path,
    model_size: str = DEFAULT_WHISPER_MODEL,
    language: Optional[str] = None,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Transcribe an audio file using faster-whisper.
    Args:
        audio_path: Path to the audio file.
        model_size: tiny, base, small, etc.
        language: ISO-639-1 code (e.g. 'en') or None/empty for auto-detect.
        device: 'cpu' or 'cuda'.
        compute_type: 'int8' or 'float16'.
        progress_callback: Optional callable(percent_complete: float, message: str).
    Returns:
        dict: {
            "transcript_text": str,
            "segments": List[dict: {id, start, end, text}],
            "detected_language": str,
            "language_probability": float,
            "duration": float
        }
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    model = get_whisper_model(model_size=model_size, device=device, compute_type=compute_type)

    if progress_callback:
        progress_callback(10, "Whisper model loaded. Starting audio decoding...")

    transcribe_lang = language if (language and language != "auto") else None

    # Run transcription
    segments_generator, info = model.transcribe(
        str(audio_path),
        language=transcribe_lang,
        beam_size=5,
        word_timestamps=False,
        vad_filter=True,  # Filter out non-speech segments
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    detected_lang = info.language
    lang_prob = round(info.language_probability, 3)
    audio_duration = info.duration

    logger.info(
        "Detected language: %s (probability: %.2f), Duration: %.2fs",
        detected_lang,
        lang_prob,
        audio_duration,
    )

    segments: List[Dict[str, Any]] = []
    text_chunks: List[str] = []

    last_end = 0.0
    paragraph_sentences: List[str] = []
    full_paragraphs: List[str] = []

    for i, seg in enumerate(segments_generator):
        clean_text = seg.text.strip()
        if not clean_text:
            continue

        seg_dict = {
            "id": i,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": clean_text,
        }
        segments.append(seg_dict)
        paragraph_sentences.append(clean_text)

        # Create paragraph breaks if silence is longer than 2.0s or paragraph has >= 4 sentences
        silence_gap = seg.start - last_end
        if (silence_gap > 2.0 or len(paragraph_sentences) >= 4) and paragraph_sentences:
            full_paragraphs.append(" ".join(paragraph_sentences))
            paragraph_sentences = []

        last_end = seg.end

        if progress_callback and audio_duration > 0:
            pct = min(90, 10 + int((seg.end / audio_duration) * 80))
            progress_callback(pct, f"Transcribing... ({format_timestamp(seg.end)} / {format_timestamp(audio_duration)})")

    if paragraph_sentences:
        full_paragraphs.append(" ".join(paragraph_sentences))

    # Fallback to joining all segment texts if paragraph formation produced empty
    if full_paragraphs:
        formatted_transcript = "\n\n".join(full_paragraphs)
    else:
        formatted_transcript = " ".join([s["text"] for s in segments])

    if not formatted_transcript.strip():
        raise ValueError(
            "Transcription produced no text. The audio may be silent or corrupted."
        )

    if progress_callback:
        progress_callback(100, "Transcription complete!")

    return {
        "transcript_text": formatted_transcript,
        "segments": segments,
        "detected_language": detected_lang,
        "language_probability": lang_prob,
        "duration": round(audio_duration, 2),
    }


def format_timestamp(seconds: float, srt_format: bool = False) -> str:
    """Format seconds into HH:MM:SS or HH:MM:SS,mmm for SRT."""
    millis = int((seconds - int(seconds)) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if srt_format:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def segments_to_srt(segments: List[Dict[str, Any]]) -> str:
    """Generate standard SubRip (.srt) subtitle string from transcript segments."""
    srt_lines = []
    for idx, seg in enumerate(segments, start=1):
        start_str = format_timestamp(seg["start"], srt_format=True)
        end_str = format_timestamp(seg["end"], srt_format=True)
        text = seg["text"].strip()
        srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")
    return "\n".join(srt_lines)
