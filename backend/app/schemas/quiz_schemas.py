"""
Pydantic schemas for Quiz generation, submission, and grading.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    key: str = Field(..., description="Option identifier e.g. 'A', 'B', 'C', 'D'")
    text: str = Field(..., description="Option description text")


class QuizQuestionItem(BaseModel):
    id: int
    question: str
    options: List[str]  # Exactly 4 options
    explanation: Optional[str] = None
    context_source: Optional[str] = None


class QuizGenerateRequest(BaseModel):
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty_level: str = Field(default="Medium")  # Easy, Medium, Hard


class QuizResponse(BaseModel):
    quiz_id: int
    lecture_id: int
    lecture_title: str
    question_count: int
    difficulty_level: str
    questions: List[QuizQuestionItem]
    created_at: datetime


class AnswerSubmissionItem(BaseModel):
    question_id: int
    selected_option: str  # Option text or index chosen by student


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerSubmissionItem]
    time_taken_seconds: float = 0.0


class QuestionGradingResult(BaseModel):
    question_id: int
    question: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    context_source: Optional[str] = None


class QuizResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    lecture_id: int
    lecture_title: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_taken_seconds: float
    evaluations: List[QuestionGradingResult]
    completed_at: datetime
