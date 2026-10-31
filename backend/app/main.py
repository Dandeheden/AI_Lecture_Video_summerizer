"""
Main FastAPI Application entry point for LectureAI.
Provides REST endpoints, CORS middleware, database migration on startup,
and modular routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import CORS_ORIGINS
from backend.app.database.connection import Base, engine
from backend.app.api import health_router, lectures_router, quizzes_router, history_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lectureai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing LectureAI SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down LectureAI API server...")


app = FastAPI(
    title="LectureAI - Lecture Summarizer & Question Generator API",
    description="Final-Year B.Tech CSE AI Project converting lecture media to timestamped transcripts, summaries, study notes, and MCQs.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure Cross-Origin Resource Sharing (CORS) for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An internal server error occurred: {str(exc)}"}
    )

# Include API Routers with /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(lectures_router, prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/")
def root():
    return {
        "project": "AI-Powered Lecture Video Summarizer and Question Generator",
        "documentation": "/docs",
        "api_health": "/api/health"
    }
