"""Database package for LectureAI."""
from .db import (
    init_db,
    save_lecture,
    get_lecture,
    get_all_lectures,
    delete_lecture,
    update_lecture_analysis,
    save_quiz,
    get_quiz,
    get_quizzes_by_lecture,
    save_quiz_attempt,
    get_quiz_attempts,
    get_dashboard_analytics,
)

__all__ = [
    "init_db",
    "save_lecture",
    "get_lecture",
    "get_all_lectures",
    "delete_lecture",
    "update_lecture_analysis",
    "save_quiz",
    "get_quiz",
    "get_quizzes_by_lecture",
    "save_quiz_attempt",
    "get_quiz_attempts",
    "get_dashboard_analytics",
]
