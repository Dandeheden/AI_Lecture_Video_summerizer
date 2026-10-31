"""
Database operations for LectureAI.
Provides SQLite persistence for lectures, transcripts, summaries, study notes, topics, quizzes, and scores.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from config import DATABASE_PATH, BASE_DIR

logger = logging.getLogger(__name__)
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Return an open SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Initialize database tables according to schema.sql."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    logger.info("Database initialized successfully at %s", DATABASE_PATH)


# ==================== LECTURE CRUD ====================


def save_lecture(lecture_data: Dict[str, Any]) -> int:
    """
    Insert a new lecture record into the database.
    Returns the generated lecture ID.
    """
    init_db()
    sql = """
    INSERT INTO lectures (
        title, original_filename, file_type, file_size_mb, duration_seconds,
        detected_language, transcript_text, transcript_segments_json,
        short_summary, detailed_summary, bullet_notes, study_notes_json, topics_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (
                lecture_data.get("title", "Untitled Lecture"),
                lecture_data.get("original_filename", "unnamed_file"),
                lecture_data.get("file_type", "unknown"),
                float(lecture_data.get("file_size_mb", 0.0)),
                float(lecture_data.get("duration_seconds", 0.0)),
                lecture_data.get("detected_language", "en"),
                lecture_data.get("transcript_text", ""),
                json.dumps(lecture_data.get("transcript_segments", [])),
                lecture_data.get("short_summary", ""),
                lecture_data.get("detailed_summary", ""),
                lecture_data.get("bullet_notes", ""),
                json.dumps(lecture_data.get("study_notes", {})),
                json.dumps(lecture_data.get("topics", {})),
            ),
        )
        conn.commit()
        lecture_id = cursor.lastrowid
        logger.info("Saved new lecture ID %s: %s", lecture_id, lecture_data.get("title"))
        return lecture_id


def get_lecture(lecture_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single lecture record by ID with parsed JSON structures."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _format_lecture_row(row)


def get_all_lectures() -> List[Dict[str, Any]]:
    """Retrieve all saved lectures ordered by most recently processed."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lectures ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [_format_lecture_row(row) for row in rows]


def update_lecture_analysis(
    lecture_id: int,
    short_summary: Optional[str] = None,
    detailed_summary: Optional[str] = None,
    bullet_notes: Optional[str] = None,
    study_notes: Optional[Dict[str, Any]] = None,
    topics: Optional[Dict[str, Any]] = None,
) -> bool:
    """Update summarization and topic analysis for an existing lecture."""
    init_db()
    fields = []
    values = []

    if short_summary is not None:
        fields.append("short_summary = ?")
        values.append(short_summary)
    if detailed_summary is not None:
        fields.append("detailed_summary = ?")
        values.append(detailed_summary)
    if bullet_notes is not None:
        fields.append("bullet_notes = ?")
        values.append(bullet_notes)
    if study_notes is not None:
        fields.append("study_notes_json = ?")
        values.append(json.dumps(study_notes))
    if topics is not None:
        fields.append("topics_json = ?")
        values.append(json.dumps(topics))

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(lecture_id)

    sql = f"UPDATE lectures SET {', '.join(fields)} WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0


def delete_lecture(lecture_id: int) -> bool:
    """Delete a lecture and cascade-delete its quizzes and attempt logs."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        logger.info("Deleted lecture ID %s (success=%s)", lecture_id, deleted)
        return deleted


def _format_lecture_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Helper to convert sqlite row into python dict with deserialized JSON."""
    d = dict(row)
    try:
        d["transcript_segments"] = json.loads(d.get("transcript_segments_json") or "[]")
    except Exception:
        d["transcript_segments"] = []

    try:
        d["study_notes"] = json.loads(d.get("study_notes_json") or "{}")
    except Exception:
        d["study_notes"] = {}

    try:
        d["topics"] = json.loads(d.get("topics_json") or "{}")
    except Exception:
        d["topics"] = {}

    return d


# ==================== QUIZ & ATTEMPT CRUD ====================


def save_quiz(lecture_id: int, questions: List[Dict[str, Any]], difficulty: str) -> int:
    """Save a newly generated quiz associated with a lecture."""
    init_db()
    sql = """
    INSERT INTO quizzes (lecture_id, question_count, difficulty_level, questions_json)
    VALUES (?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (lecture_id, len(questions), difficulty, json.dumps(questions)))
        conn.commit()
        return cursor.lastrowid


def get_quiz(quiz_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve quiz by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["questions"] = json.loads(res.get("questions_json") or "[]")
        return res


def get_quizzes_by_lecture(lecture_id: int) -> List[Dict[str, Any]]:
    """Retrieve all quizzes generated for a specific lecture."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM quizzes WHERE lecture_id = ? ORDER BY created_at DESC",
            (lecture_id,),
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            q = dict(r)
            q["questions"] = json.loads(q.get("questions_json") or "[]")
            result.append(q)
        return result


def save_quiz_attempt(attempt_data: Dict[str, Any]) -> int:
    """
    Save a student's quiz attempt and computed score.
    """
    init_db()
    sql = """
    INSERT INTO quiz_attempts (
        quiz_id, lecture_id, total_questions, correct_answers,
        score_percentage, answers_json, time_taken_seconds
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (
                attempt_data.get("quiz_id"),
                attempt_data["lecture_id"],
                attempt_data["total_questions"],
                attempt_data["correct_answers"],
                float(attempt_data["score_percentage"]),
                json.dumps(attempt_data.get("answers", [])),
                float(attempt_data.get("time_taken_seconds", 0.0)),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_quiz_attempts(lecture_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve quiz attempt history, optionally filtered by lecture."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        if lecture_id is not None:
            sql = """
            SELECT qa.*, l.title AS lecture_title
            FROM quiz_attempts qa
            JOIN lectures l ON qa.lecture_id = l.id
            WHERE qa.lecture_id = ?
            ORDER BY qa.completed_at DESC
            """
            cursor.execute(sql, (lecture_id,))
        else:
            sql = """
            SELECT qa.*, l.title AS lecture_title
            FROM quiz_attempts qa
            JOIN lectures l ON qa.lecture_id = l.id
            ORDER BY qa.completed_at DESC
            """
            cursor.execute(sql)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            att = dict(r)
            try:
                att["answers"] = json.loads(att.get("answers_json") or "[]")
            except Exception:
                att["answers"] = []
            result.append(att)
        return result


# ==================== ANALYTICS AGGREGATES ====================


def get_dashboard_analytics() -> Dict[str, Any]:
    """Calculate aggregate statistics for dashboard and analytics views."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Lecture stats
        cursor.execute("SELECT COUNT(*) FROM lectures")
        total_lectures = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM lectures WHERE short_summary IS NOT NULL AND LENGTH(short_summary) > 0"
        )
        total_notes = cursor.fetchone()[0]

        # Quiz stats
        cursor.execute("SELECT COUNT(*), AVG(score_percentage), MAX(score_percentage) FROM quiz_attempts")
        att_row = cursor.fetchone()
        total_quizzes_attempted = att_row[0] or 0
        avg_score = round(att_row[1], 1) if att_row[1] is not None else 0.0
        max_score = round(att_row[2], 1) if att_row[2] is not None else 0.0

        # Recent attempts
        cursor.execute(
            """
            SELECT qa.id, qa.score_percentage, qa.completed_at, l.title AS lecture_title
            FROM quiz_attempts qa
            JOIN lectures l ON qa.lecture_id = l.id
            ORDER BY qa.completed_at DESC
            LIMIT 10
            """
        )
        recent_attempts = [dict(r) for r in cursor.fetchall()]

        # Recent lectures
        cursor.execute(
            """
            SELECT id, title, file_type, file_size_mb, detected_language, created_at
            FROM lectures
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        recent_lectures = [dict(r) for r in cursor.fetchall()]

        return {
            "total_lectures": total_lectures,
            "total_notes": total_notes,
            "total_quizzes_attempted": total_quizzes_attempted,
            "average_score": avg_score,
            "highest_score": max_score,
            "recent_attempts": recent_attempts,
            "recent_lectures": recent_lectures,
        }
