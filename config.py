"""
Configuration module for LectureAI - Smart Lecture Summarizer & Quiz Generator.
Contains application constants, file path definitions, model defaults, and UI themes.
"""

from pathlib import Path
import os
import torch

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Application Info
APP_NAME = "LectureAI"
APP_TAGLINE = "Turn lectures into knowledge."
APP_VERSION = "1.0.0"

# Storage & Cache Directories
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "lectureai.db"
TEMP_DIR = DATA_DIR / "temp"
EXPORTS_DIR = DATA_DIR / "exports"
MODELS_CACHE_DIR = DATA_DIR / "models_cache"

# Ensure runtime directories exist
for path in [DATA_DIR, TEMP_DIR, EXPORTS_DIR, MODELS_CACHE_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Hardware Acceleration
CUDA_AVAILABLE = torch.cuda.is_available()
DEFAULT_DEVICE = "cuda" if CUDA_AVAILABLE else "cpu"
DEFAULT_COMPUTE_TYPE = "float16" if CUDA_AVAILABLE else "int8"

# File Processing Limits
MAX_UPLOAD_SIZE_MB = 250
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]
SUPPORTED_TEXT_FORMATS = [".txt"]
ALL_SUPPORTED_FORMATS = (
    SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS + SUPPORTED_TEXT_FORMATS
)

# Speech Recognition (faster-whisper) Settings
WHISPER_MODELS = {
    "tiny": {
        "name": "tiny",
        "description": "Fastest, lowest memory (~75MB), ideal for testing and quick drafts",
        "ram_gb": 0.5,
    },
    "base": {
        "name": "base",
        "description": "Balanced speed and accuracy (~145MB), recommended default",
        "ram_gb": 1.0,
    },
    "small": {
        "name": "small",
        "description": "High accuracy for lectures with technical terms (~480MB)",
        "ram_gb": 2.0,
    },
    "medium": {
        "name": "medium",
        "description": "Superior accuracy for complex multilingual lectures (~1.5GB)",
        "ram_gb": 4.5,
    },
}
DEFAULT_WHISPER_MODEL = "base"

# Supported Speech Languages for UI Dropdown
SUPPORTED_LANGUAGES = {
    "auto": "Automatic Detection",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "zh": "Chinese",
    "ja": "Japanese",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
}

# Summarization Model Presets
SUMMARIZATION_MODELS = {
    "distilbart": {
        "name": "sshleifer/distilbart-cnn-12-6",
        "label": "DistilBART CNN (Lightweight, ~1.2GB)",
        "description": "Fast, high-quality news & academic summarization with lower RAM usage.",
        "max_input_length": 1024,
    },
    "flan-t5-small": {
        "name": "google/flan-t5-small",
        "label": "Google FLAN-T5 Small (Ultra-light, ~300MB)",
        "description": "Compact sequence-to-sequence model ideal for resource-constrained systems.",
        "max_input_length": 512,
    },
    "flan-t5-base": {
        "name": "google/flan-t5-base",
        "label": "Google FLAN-T5 Base (Recommended, ~990MB)",
        "description": "Versatile instruction-tuned model providing structured reasoning and notes.",
        "max_input_length": 1024,
    },
    "bart-large-cnn": {
        "name": "facebook/bart-large-cnn",
        "label": "Facebook BART Large CNN (~1.6GB)",
        "description": "State-of-the-art abstractive summarizer with deep contextual coherence.",
        "max_input_length": 1024,
    },
}
DEFAULT_SUMMARIZATION_MODEL = "distilbart"

# Summarization Length Word Targets
SUMMARY_LENGTH_CONFIG = {
    "Short": {"min_words": 60, "max_words": 150, "target_reduction": 0.15},
    "Medium": {"min_words": 150, "max_words": 350, "target_reduction": 0.35},
    "Detailed": {"min_words": 350, "max_words": 750, "target_reduction": 0.60},
}

# Quiz Generation Presets
QUIZ_QUESTION_COUNTS = [5, 10, 15, 20]
QUIZ_DIFFICULTIES = ["Easy", "Medium", "Hard"]
QUIZ_TYPES = ["Multiple Choice", "True / False", "Short Answer"]

# UI Color Palette & Styling
THEME = {
    "primary": "#8b5cf6",
    "primary_hover": "#7c3aed",
    "secondary": "#6366f1",
    "accent": "#38bdf8",
    "background": "#0b0f19",
    "card_bg": "#131b2e",
    "surface": "#1e293b",
    "text": "#f8fafc",
    "text_muted": "#94a3b8",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
}
