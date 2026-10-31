"""
Unit tests for upload validation, file extension filtering, and limits.
"""

from pathlib import Path
from backend.app.config import SUPPORTED_EXTENSIONS, MAX_UPLOAD_SIZE_MB


def test_supported_extensions():
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".webm" in SUPPORTED_EXTENSIONS
    assert ".mp3" in SUPPORTED_EXTENSIONS
    assert ".wav" in SUPPORTED_EXTENSIONS
    assert ".exe" not in SUPPORTED_EXTENSIONS
    assert ".pdf" not in SUPPORTED_EXTENSIONS


def test_max_upload_size_configured():
    assert MAX_UPLOAD_SIZE_MB >= 50
    assert MAX_UPLOAD_SIZE_MB <= 1000
