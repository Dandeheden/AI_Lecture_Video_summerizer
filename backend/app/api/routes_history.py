"""
History and analytical metrics API routes.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.connection import get_db
from backend.app.models.db_models import Lecture, Quiz, QuizAttempt
from backend.app.schemas.lecture_schemas import (
    LectureHistoryResponse,
    LectureHistoryItem,
)

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=LectureHistoryResponse)
def get_all_lecture_history(db: Session = Depends(get_db)):
    """Retrieve full history of uploaded lectures, their statuses, and metadata."""
    lectures = db.query(Lecture).order_by(Lecture.created_at.desc()).all()

    items = []
    for lec in lectures:
        has_trans = bool(lec.transcript_text and len(lec.transcript_text.strip()) > 0)
        has_summ = bool(lec.short_summary and len(lec.short_summary.strip()) > 0)
        has_qz = bool(lec.quizzes and len(lec.quizzes) > 0)

        items.append(
            LectureHistoryItem(
                id=lec.id,
                title=lec.title,
                original_filename=lec.original_filename,
                file_type=lec.file_type,
                file_size_mb=lec.file_size_mb,
                duration_seconds=lec.duration_seconds,
                detected_language=lec.detected_language,
                status=lec.status,
                progress_percent=lec.progress_percent,
                has_transcript=has_trans,
                has_summary=has_summ,
                has_quiz=has_qz,
                created_at=lec.created_at,
                updated_at=lec.updated_at
            )
        )

    return LectureHistoryResponse(
        total_lectures=len(items),
        lectures=items
    )


@router.get("/stats")
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """Retrieve high-level dashboard aggregate metrics."""
    total_lectures = db.query(Lecture).count()
    completed_lectures = db.query(Lecture).filter(Lecture.status == "completed").count()

    # Sum total lecture duration
    total_duration_sec = db.query(func.sum(Lecture.duration_seconds)).scalar() or 0.0

    # Quiz attempts statistics
    total_attempts = db.query(QuizAttempt).count()
    avg_score = db.query(func.avg(QuizAttempt.score_percentage)).scalar() or 0.0

    # Recent 5 attempts
    recent_attempts = (
        db.query(QuizAttempt)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(5)
        .all()
    )

    recent_attempts_data = []
    for a in recent_attempts:
        lec = db.query(Lecture).filter(Lecture.id == a.lecture_id).first()
        recent_attempts_data.append({
            "attempt_id": a.id,
            "quiz_id": a.quiz_id,
            "lecture_id": a.lecture_id,
            "lecture_title": lec.title if lec else "Lecture",
            "score_percentage": a.score_percentage,
            "total_questions": a.total_questions,
            "correct_answers": a.correct_answers,
            "completed_at": a.completed_at
        })

    return {
        "total_lectures": total_lectures,
        "completed_lectures": completed_lectures,
        "total_minutes_processed": round(total_duration_sec / 60.0, 1),
        "total_quizzes_taken": total_attempts,
        "average_quiz_score": round(avg_score, 1),
        "recent_attempts": recent_attempts_data
    }
