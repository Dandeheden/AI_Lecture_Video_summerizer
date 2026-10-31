"""
File processing and media extraction module for LectureAI.
Handles file validation, audio extraction from video via FFmpeg, temporary storage, and cleanup.
"""

import os
import shutil
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from config import (
    MAX_UPLOAD_SIZE_MB,
    SUPPORTED_VIDEO_FORMATS,
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_TEXT_FORMATS,
    TEMP_DIR,
)

logger = logging.getLogger(__name__)


def get_ffmpeg_executable() -> Optional[str]:
    """
    Locate a valid FFmpeg binary.
    Checks system PATH first, then imageio_ffmpeg bundled binary.
    """
    # 1. System PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 2. imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception as e:
        logger.debug("imageio_ffmpeg check failed: %s", e)

    return None


def is_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system."""
    return get_ffmpeg_executable() is not None


def validate_uploaded_file(uploaded_file) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate an uploaded file's extension, size, and presence.
    Returns:
        (is_valid: bool, error_message: Optional[str], metadata: dict)
    """
    if uploaded_file is None:
        return False, "No file was uploaded.", {}

    filename = uploaded_file.name
    file_size_bytes = uploaded_file.size
    file_size_mb = file_size_bytes / (1024 * 1024)
    file_ext = Path(filename).suffix.lower()

    metadata = {
        "filename": filename,
        "extension": file_ext,
        "size_bytes": file_size_bytes,
        "size_mb": round(file_size_mb, 2),
        "is_video": file_ext in SUPPORTED_VIDEO_FORMATS,
        "is_audio": file_ext in SUPPORTED_AUDIO_FORMATS,
        "is_text": file_ext in SUPPORTED_TEXT_FORMATS,
    }

    # Format check
    if not (metadata["is_video"] or metadata["is_audio"] or metadata["is_text"]):
        allowed = ", ".join(
            SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS + SUPPORTED_TEXT_FORMATS
        )
        return (
            False,
            f"Unsupported file format '{file_ext}'. Supported formats: {allowed}",
            metadata,
        )

    # Empty check
    if file_size_bytes == 0:
        return False, "Uploaded file is empty (0 bytes).", metadata

    # Size check
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        return (
            False,
            f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB} MB.",
            metadata,
        )

    # Video check for FFmpeg requirement
    if metadata["is_video"] and not is_ffmpeg_available():
        return (
            False,
            "FFmpeg is required to process video files but was not found. "
            "Please upload an audio file (.mp3, .wav) or text transcript (.txt), "
            "or install FFmpeg / imageio-ffmpeg.",
            metadata,
        )

    return True, None, metadata


def save_uploaded_file_to_temp(uploaded_file) -> Path:
    """
    Stream uploaded file to a temporary file in TEMP_DIR.
    Avoids holding entire file in memory.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix.lower()
    temp_file = tempfile.NamedTemporaryFile(
        dir=TEMP_DIR, prefix="upload_", suffix=suffix, delete=False
    )
    temp_path = Path(temp_file.name)

    uploaded_file.seek(0)
    # Stream in 1MB chunks
    while True:
        chunk = uploaded_file.read(1024 * 1024)
        if not chunk:
            break
        temp_file.write(chunk)
    temp_file.close()
    return temp_path


def extract_audio_from_video(video_path: Path, output_format: str = "wav") -> Tuple[Path, float]:
    """
    Extract audio track from video file using FFmpeg into a 16kHz mono audio file.
    Returns:
        (extracted_audio_path, duration_seconds)
    """
    ffmpeg_exe = get_ffmpeg_executable()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg executable not found. Unable to extract audio.")

    output_path = TEMP_DIR / f"{video_path.stem}_audio.{output_format}"

    # Command: ffmpeg -y -i input -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]

    logger.info("Extracting audio: %s", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg error: %s", result.stderr)
        raise RuntimeError(f"Audio extraction failed: {result.stderr[-300:]}")

    duration = get_audio_duration(output_path)
    return output_path, duration


def get_audio_duration(audio_path: Path) -> float:
    """Estimate or measure audio duration in seconds."""
    # Try wave module if it's a WAV file
    if audio_path.suffix.lower() == ".wav":
        try:
            import wave
            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
        except Exception as e:
            logger.debug("wave read duration failed: %s", e)

    # Fallback to ffprobe/ffmpeg if available
    ffmpeg_exe = get_ffmpeg_executable()
    if ffmpeg_exe:
        try:
            cmd = [ffmpeg_exe, "-i", str(audio_path)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Find Duration: 00:00:00.00 in stderr
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    time_str = line.split("Duration:")[1].split(",")[0].strip()
                    parts = time_str.split(":")
                    if len(parts) == 3:
                        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                        return round(h * 3600 + m * 60 + s, 2)
        except Exception as e:
            logger.debug("ffmpeg duration parse failed: %s", e)

    return 0.0


def read_text_transcript(file_path: Path) -> str:
    """Read a plain text transcript with robust encoding fallback."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def cleanup_temp_files(*paths: Optional[Path]) -> None:
    """Safely delete temporary files."""
    for p in paths:
        if p and p.exists():
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
                logger.debug("Cleaned up temp path: %s", p)
            except Exception as e:
                logger.warning("Failed to clean up %s: %s", p, e)
