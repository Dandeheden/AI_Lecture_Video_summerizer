"""
Functional and integration tests for FastAPI route handlers and database operations.
Directly exercises route handlers and SQLite session logic.
"""

from backend.app.main import root
from backend.app.api.routes_health import get_health_status
from backend.app.api.routes_history import get_all_lecture_history, get_dashboard_statistics
from backend.app.database.connection import SessionLocal, Base, engine
from backend.app.models.db_models import Lecture


def test_root_endpoint():
    res = root()
    assert "project" in res
    assert "api_health" in res


def test_health_endpoint():
    res = get_health_status()
    assert res["status"] == "online"
    assert "hardware" in res
    assert "default_models" in res


def test_history_and_stats_endpoints():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Test get_all_lecture_history
        history = get_all_lecture_history(db=db)
        assert hasattr(history, "total_lectures")
        assert hasattr(history, "lectures")
        assert isinstance(history.lectures, list)

        # Test get_dashboard_statistics
        stats = get_dashboard_statistics(db=db)
        assert "total_lectures" in stats
        assert "completed_lectures" in stats
        assert "total_minutes_processed" in stats
        assert "total_quizzes_taken" in stats
    finally:
        db.close()


def test_database_lecture_persistence():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        test_lec = Lecture(
            title="Automated Test Lecture",
            original_filename="test_lec.mp4",
            stored_filename="stored_test_lec.mp4",
            file_type="video",
            file_size_mb=12.5,
            duration_seconds=180.0,
            status="completed",
            progress_percent=100,
            transcript_text="Test transcript content.",
            short_summary="Test short summary."
        )
        db.add(test_lec)
        db.commit()
        db.refresh(test_lec)

        # Query back
        retrieved = db.query(Lecture).filter(Lecture.id == test_lec.id).first()
        assert retrieved is not None
        assert retrieved.title == "Automated Test Lecture"
        assert retrieved.status == "completed"

        # Cleanup
        db.delete(retrieved)
        db.commit()
    finally:
        db.close()
