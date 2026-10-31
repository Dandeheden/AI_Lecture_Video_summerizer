from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_lectures import router as lectures_router
from backend.app.api.routes_quizzes import router as quizzes_router
from backend.app.api.routes_history import router as history_router

__all__ = ["health_router", "lectures_router", "quizzes_router", "history_router"]
