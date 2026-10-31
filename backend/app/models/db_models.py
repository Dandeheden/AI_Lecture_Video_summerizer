"""
SQLAlchemy database models for LectureAI.
Defines schemas for Lectures, Quizzes, and Quiz Attempts.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="Untitled Lecture")
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_mb = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    detected_language = Column(String(20), default="en")

    # Processing lifecycle state
    # States: uploaded, transcribing, summarizing, generating_questions, completed, failed
    status = Column(String(50), default="uploaded", index=True)
    progress_percent = Column(Integer, default=0)
    status_message = Column(String(255), default="Upload complete. Ready for processing.")
    error_message = Column(Text, nullable=True)

    # Generated Content
    transcript_text = Column(Text, default="")
    transcript_segments_json = Column(Text, default="[]")  # list of {start, end, text}
    short_summary = Column(Text, default="")
    detailed_summary = Column(Text, default="")
    bullet_notes = Column(Text, default="")
    study_notes_json = Column(Text, default="{}")  # {concepts, definitions, key_takeaways, exam_prep}
    topics_json = Column(Text, default="{}")  # {main_topics, subtopics, keywords}

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quizzes = relationship("Quiz", back_populates="lecture", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="lecture", cascade="all, delete-orphan")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    question_count = Column(Integer, nullable=False, default=5)
    difficulty_level = Column(String(50), default="Medium")
    # JSON array of question objects:
    # [{id, question, options: [A, B, C, D], correct_answer: "A", explanation, context_source}]
    questions_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lecture = relationship("Lecture", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    # JSON array of answer evaluations:
    # [{question_id, user_answer, correct_answer, is_correct, explanation}]
    answers_json = Column(Text, nullable=False, default="[]")
    time_taken_seconds = Column(Float, default=0.0)
    completed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    lecture = relationship("Lecture", back_populates="attempts")
