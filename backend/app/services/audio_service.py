"""
Audio extraction and media utility service for LectureAI.
Uses system FFmpeg or imageio-ffmpeg bundled binary.
"""

import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_ffmpeg_executable() -> Optional[str]:
    """Locate a working FFmpeg binary: checks system PATH, then imageio_ffmpeg."""
    # 1. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 2. Check imageio_ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception as e:
        logger.debug("imageio_ffmpeg executable lookup failed: %s", e)

    return None


def is_ffmpeg_available() -> bool:
    """Check if a valid FFmpeg binary is available."""
    return get_ffmpeg_executable() is not None


def extract_audio_from_media(input_path: Path, output_wav_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Extracts or normalizes audio from video/audio to 16kHz mono WAV format,
    which is optimal for Whisper speech recognition.
    """
    ffmpeg_exe = get_ffmpeg_executable()
    if not ffmpeg_exe:
        return False, "FFmpeg binary not found. Please install ffmpeg or imageio-ffmpeg."

    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_exe,
        "-y",               # overwrite without asking
        "-i", str(input_path),
        "-vn",              # disable video
        "-acodec", "pcm_s16le", # standard PCM 16-bit
        "-ar", "16000",     # 16kHz sample rate
        "-ac", "1",         # 1 mono channel
        str(output_wav_path),
    ]

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=180
        )
        if process.returncode != 0:
            logger.error("FFmpeg error: %s", process.stderr)
            return False, f"FFmpeg failed with exit code {process.returncode}: {process.stderr[:300]}"
        return True, None
    except Exception as e:
        logger.exception("Audio extraction failed for %s", input_path)
        return False, str(e)


def get_media_duration_seconds(file_path: Path) -> float:
    """Approximate duration of audio file via wave module or file size estimation."""
    try:
        import wave
        with wave.open(str(file_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return round(frames / float(rate), 2)
    except Exception:
        pass
    return 0.0
