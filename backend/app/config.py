"""
Configuration module for LectureAI Backend.
Defines storage paths, model defaults, device allocation, and API settings.
"""

from pathlib import Path
import os
import torch

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = BACKEND_DIR / "uploads"
OUTPUTS_DIR = BACKEND_DIR / "outputs"
MODELS_CACHE_DIR = DATA_DIR / "models_cache"
DATABASE_PATH = DATA_DIR / "lectureai.db"

# Ensure essential directories exist
for path in [DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR, MODELS_CACHE_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Hardware Acceleration
CUDA_AVAILABLE = torch.cuda.is_available()
DEFAULT_DEVICE = os.getenv("DEVICE", "cuda" if CUDA_AVAILABLE else "cpu")
DEFAULT_COMPUTE_TYPE = "float16" if DEFAULT_DEVICE == "cuda" else "int8"

# Upload and Processing Limits
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 250))
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
SUPPORTED_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS.union(SUPPORTED_AUDIO_EXTENSIONS)

# Speech Recognition (faster-whisper)
WHISPER_MODELS = {
    "tiny": {"name": "tiny", "description": "Fastest (~75MB), minimal RAM"},
    "base": {"name": "base", "description": "Balanced speed & accuracy (~145MB), recommended default"},
    "small": {"name": "small", "description": "High accuracy for technical lectures (~480MB)"},
    "medium": {"name": "medium", "description": "Superior accuracy (~1.5GB)"},
}
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL_SIZE", "base")

# Summarization Models (Hugging Face)
SUMMARIZATION_MODELS = {
    "distilbart": {
        "name": "sshleifer/distilbart-cnn-12-6",
        "label": "DistilBART CNN (Lightweight, ~1.2GB)",
        "max_input_length": 1024,
    },
    "flan-t5-small": {
        "name": "google/flan-t5-small",
        "label": "Google FLAN-T5 Small (Compact, ~300MB)",
        "max_input_length": 512,
    },
    "flan-t5-base": {
        "name": "google/flan-t5-base",
        "label": "Google FLAN-T5 Base (~990MB)",
        "max_input_length": 1024,
    },
    "bart-large-cnn": {
        "name": "facebook/bart-large-cnn",
        "label": "Facebook BART Large CNN (~1.6GB)",
        "max_input_length": 1024,
    },
}
DEFAULT_SUMMARIZATION_MODEL = os.getenv("DEFAULT_SUMMARIZATION_MODEL", "distilbart")

# CORS Origins
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",")
    if origin.strip()
]
