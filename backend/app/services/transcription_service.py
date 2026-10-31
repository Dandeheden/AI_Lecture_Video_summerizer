"""
Speech recognition service using faster-whisper.
Converts lecture audio files into timestamped transcripts.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from backend.app.config import (
    DEFAULT_WHISPER_MODEL,
    DEFAULT_DEVICE,
    DEFAULT_COMPUTE_TYPE,
    MODELS_CACHE_DIR,
)

logger = logging.getLogger(__name__)

# In-memory model cache to avoid re-initializing weights on every API request
_MODEL_CACHE: Dict[str, Any] = {}


def get_whisper_model(
    model_size: str = DEFAULT_WHISPER_MODEL,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
):
    """
    Retrieves or lazily loads a faster-whisper WhisperModel instance.
    """
    from faster_whisper import WhisperModel

    cache_key = f"{model_size}_{device}_{compute_type}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    logger.info("Loading faster-whisper model '%s' (device=%s, compute_type=%s)...", model_size, device, compute_type)

    try:
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(MODELS_CACHE_DIR),
        )
        _MODEL_CACHE[cache_key] = model
        return model
    except Exception as e:
        logger.warning(
            "Failed to load Whisper '%s' with compute_type '%s': %s. Retrying on CPU with 'int8'...",
            model_size,
            compute_type,
            e,
        )
        # Fallback to cpu int8
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(MODELS_CACHE_DIR),
        )
        _MODEL_CACHE[cache_key] = model
        return model


def transcribe_audio_file(
    audio_path: Path,
    model_size: str = DEFAULT_WHISPER_MODEL,
    language: Optional[str] = None,
    beam_size: int = 5,
) -> Dict[str, Any]:
    """
    Transcribes audio to text with timestamps and detected language.

    Returns:
        {
            "transcript_text": str,
            "segments": [{"start": float, "end": float, "text": str}],
            "detected_language": str,
            "duration_seconds": float
        }
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    model = get_whisper_model(model_size=model_size)

    # Convert language 'auto' to None so Whisper auto-detects
    target_lang = None if (not language or language.lower() in ("auto", "none")) else language.lower()

    logger.info("Starting Whisper transcription on %s (lang=%s)...", audio_path.name, target_lang)

    segments_gen, info = model.transcribe(
        str(audio_path),
        beam_size=beam_size,
        language=target_lang,
        vad_filter=True, # Voice Activity Detection to filter background noise
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    detected_lang = info.language if hasattr(info, "language") else "en"
    duration = getattr(info, "duration", 0.0)

    segments_list = []
    text_chunks = []

    for seg in segments_gen:
        cleaned_text = seg.text.strip()
        if cleaned_text:
            segments_list.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": cleaned_text,
            })
            text_chunks.append(cleaned_text)

    full_transcript = " ".join(text_chunks).strip()

    return {
        "transcript_text": full_transcript,
        "segments": segments_list,
        "detected_language": detected_lang,
        "duration_seconds": round(duration, 2),
    }
