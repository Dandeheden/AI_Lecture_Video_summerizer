"""
Unit tests for MCQ synthesis, distinct options validation, and server-side grading.
"""

from backend.app.services.quiz_service import (
    generate_mcqs_from_text,
    evaluate_quiz_submission,
)


def test_mcq_generation_options_and_structure():
    text = (
        "Convolutional Layer is defined as an operation that applies spatial sliding kernels across input feature maps. "
        "Max Pooling is used to downsample spatial dimensions and control overfitting. "
        "The Adam Optimizer combines momentum and RMSProp for adaptive learning rates."
    )
    mcqs = generate_mcqs_from_text(transcript_text=text, summary_text=text, num_questions=3)
    assert len(mcqs) > 0

    for q in mcqs:
        assert len(q["options"]) == 4
        # Verify all 4 options are strictly unique
        assert len(set(q["options"])) == 4
        assert q["correct_answer"] in q["options"]
        assert len(q["explanation"]) > 0


def test_server_side_quiz_grading():
    stored_questions = [
        {
            "id": 1,
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": "4",
            "explanation": "Basic arithmetic."
        },
        {
            "id": 2,
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Rome"],
            "correct_answer": "Paris",
            "explanation": "Geography fact."
        }
    ]

    user_answers = [
        {"question_id": 1, "selected_option": "4"},       # Correct
        {"question_id": 2, "selected_option": "London"},  # Incorrect
    ]

    result = evaluate_quiz_submission(stored_questions, user_answers, time_taken=45.2)

    assert result["total_questions"] == 2
    assert result["correct_answers"] == 1
    assert result["score_percentage"] == 50.0
    assert result["time_taken_seconds"] == 45.2
    assert result["evaluations"][0]["is_correct"] is True
    assert result["evaluations"][1]["is_correct"] is False
