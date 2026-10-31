"""
Quiz generation, interaction, and grading API routes.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.db_models import Lecture, Quiz, QuizAttempt
from backend.app.schemas.quiz_schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizQuestionItem,
    QuestionGradingResult,
)
from backend.app.services.quiz_service import (
    generate_mcqs_from_text,
    evaluate_quiz_submission,
)

router = APIRouter(tags=["Quizzes"])


@router.post("/lectures/{lecture_id}/quiz", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_lecture_quiz(
    lecture_id: int,
    request: QuizGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate interactive MCQs grounded in the lecture transcript and summary.
    Supports setting number of questions and difficulty level.
    """
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    if not lecture.transcript_text and not lecture.short_summary:
        raise HTTPException(
            status_code=400,
            detail="Lecture has no transcript or summary content yet. Please wait for processing to finish."
        )

    # Synthesize MCQs
    mcqs = generate_mcqs_from_text(
        transcript_text=lecture.transcript_text,
        summary_text=lecture.short_summary or lecture.detailed_summary,
        num_questions=request.question_count,
        difficulty=request.difficulty_level
    )

    if not mcqs:
        raise HTTPException(status_code=500, detail="Failed to synthesize quiz questions from lecture text.")

    # Save Quiz to database
    quiz = Quiz(
        lecture_id=lecture.id,
        question_count=len(mcqs),
        difficulty_level=request.difficulty_level,
        questions_json=json.dumps(mcqs)
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Mask correct answers in questions returned for taking the quiz
    public_questions = []
    for q in mcqs:
        public_questions.append(
            QuizQuestionItem(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                explanation=None, # hidden until submitted
                context_source=None
            )
        )

    return QuizResponse(
        quiz_id=quiz.id,
        lecture_id=lecture.id,
        lecture_title=lecture.title,
        question_count=len(public_questions),
        difficulty_level=quiz.difficulty_level,
        questions=public_questions,
        created_at=quiz.created_at
    )


@router.get("/lectures/{lecture_id}/quiz", response_model=QuizResponse)
def get_latest_lecture_quiz(lecture_id: int, db: Session = Depends(get_db)):
    """Retrieve the most recently generated quiz for a given lecture."""
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found.")

    quiz = db.query(Quiz).filter(Quiz.lecture_id == lecture_id).order_by(Quiz.created_at.desc()).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="No quiz has been generated for this lecture yet.")

    try:
        raw_mcqs = json.loads(quiz.questions_json or "[]")
    except Exception:
        raw_mcqs = []

    public_questions = [
        QuizQuestionItem(
            id=q["id"],
            question=q["question"],
            options=q["options"],
            explanation=None,
            context_source=None
        )
        for q in raw_mcqs
    ]

    return QuizResponse(
        quiz_id=quiz.id,
        lecture_id=lecture.id,
        lecture_title=lecture.title,
        question_count=len(public_questions),
        difficulty_level=quiz.difficulty_level,
        questions=public_questions,
        created_at=quiz.created_at
    )


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz_answers(
    quiz_id: int,
    submission: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submits student answers for server-side evaluation.
    Computes total score, percentage, and detailed feedback per question with explanations.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    lecture = db.query(Lecture).filter(Lecture.id == quiz.lecture_id).first()
    lecture_title = lecture.title if lecture else "Unknown Lecture"

    try:
        stored_questions = json.loads(quiz.questions_json or "[]")
    except Exception:
        stored_questions = []

    user_answers_dict = [a.model_dump() for a in submission.answers]

    # Evaluate on the backend
    eval_result = evaluate_quiz_submission(
        stored_questions=stored_questions,
        user_answers=user_answers_dict,
        time_taken=submission.time_taken_seconds
    )

    # Persist attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        lecture_id=quiz.lecture_id,
        total_questions=eval_result["total_questions"],
        correct_answers=eval_result["correct_answers"],
        score_percentage=eval_result["score_percentage"],
        answers_json=json.dumps(eval_result["evaluations"]),
        time_taken_seconds=eval_result["time_taken_seconds"]
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    evaluations_objs = [QuestionGradingResult(**item) for item in eval_result["evaluations"]]

    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        lecture_id=quiz.lecture_id,
        lecture_title=lecture_title,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        score_percentage=attempt.score_percentage,
        time_taken_seconds=attempt.time_taken_seconds,
        evaluations=evaluations_objs,
        completed_at=attempt.completed_at
    )


@router.get("/quizzes/{quiz_id}/attempts/{attempt_id}", response_model=QuizResultResponse)
def get_quiz_attempt(
    quiz_id: int,
    attempt_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve detailed results of a prior quiz attempt."""
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.quiz_id == quiz_id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found.")

    lecture = db.query(Lecture).filter(Lecture.id == attempt.lecture_id).first()
    lecture_title = lecture.title if lecture else "Unknown Lecture"

    try:
        evaluations_raw = json.loads(attempt.answers_json or "[]")
        evaluations = [QuestionGradingResult(**item) for item in evaluations_raw]
    except Exception:
        evaluations = []

    return QuizResultResponse(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        lecture_id=attempt.lecture_id,
        lecture_title=lecture_title,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        score_percentage=attempt.score_percentage,
        time_taken_seconds=attempt.time_taken_seconds,
        evaluations=evaluations,
        completed_at=attempt.completed_at
    )
