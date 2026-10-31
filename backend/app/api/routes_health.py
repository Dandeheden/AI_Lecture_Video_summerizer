"""
Health and system status routes.
"""

from fastapi import APIRouter
from backend.app.config import (
    CUDA_AVAILABLE,
    DEFAULT_DEVICE,
    DEFAULT_WHISPER_MODEL,
    DEFAULT_SUMMARIZATION_MODEL,
)
from backend.app.services.audio_service import is_ffmpeg_available

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health_status():
    """System health check and diagnostic information."""
    return {
        "status": "online",
        "service": "LectureAI API",
        "version": "1.0.0",
        "hardware": {
            "cuda_available": CUDA_AVAILABLE,
            "device": DEFAULT_DEVICE,
            "ffmpeg_installed": is_ffmpeg_available(),
        },
        "default_models": {
            "whisper": DEFAULT_WHISPER_MODEL,
            "summarizer": DEFAULT_SUMMARIZATION_MODEL,
        }
    }
