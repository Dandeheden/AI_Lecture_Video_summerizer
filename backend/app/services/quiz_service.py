"""
Automatic Multiple-Choice Question (MCQ) Generation and Grading Service.
Generates grounded questions from lecture content with:
- 4 distinct options
- Verified correct answer
- Clear academic explanation
- Grounded lecture context passage
- Backend submission grading & scoring
"""

import re
import random
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_candidate_facts(text: str) -> List[Dict[str, Any]]:
    """
    Identifies high-yield factual sentences suitable for educational question generation:
    - Sentences containing definitions ('is defined as', 'refers to', 'is a')
    - Sentences containing core causal/functional claims ('used to', 'enables', 'allows', 'consists of')
    - Sentences with key numerical/categorical facts
    """
    sentence_pattern = r"(?<=[.!?])\s+"
    raw_sentences = [s.strip() for s in re.split(sentence_pattern, text) if s.strip()]

    candidates = []

    # Regex patterns for key statements
    def_pattern = re.compile(
        r"^([A-Z][a-zA-Z0-9\s\-]{2,35})\s+(?:is defined as|refers to|means|is essentially)\s+([^.]+)",
        re.IGNORECASE
    )
    is_a_pattern = re.compile(
        r"^([A-Z][a-zA-Z0-9\s\-]{2,35})\s+(?:is an?|are)\s+([^.]+)",
        re.IGNORECASE
    )
    role_pattern = re.compile(
        r"([A-Z][a-zA-Z0-9\s\-]{2,35})\s+(?:is used to|functions to|helps to|enables|allows)\s+([^.]+)",
        re.IGNORECASE
    )

    for s in raw_sentences:
        words = s.split()
        if len(words) < 6 or len(words) > 50:
            continue

        # Check definition
        m_def = def_pattern.search(s)
        if m_def:
            subject = m_def.group(1).strip()
            predicate = m_def.group(2).strip()
            if subject.lower() not in ["it", "this", "that", "these", "there", "what", "which"]:
                candidates.append({
                    "type": "definition",
                    "subject": subject.title(),
                    "predicate": predicate,
                    "sentence": s
                })
                continue

        # Check functional role
        m_role = role_pattern.search(s)
        if m_role:
            subject = m_role.group(1).strip()
            predicate = m_role.group(2).strip()
            if subject.lower() not in ["it", "this", "that", "these", "there"]:
                candidates.append({
                    "type": "function",
                    "subject": subject.title(),
                    "predicate": predicate,
                    "sentence": s
                })
                continue

        # Check is-a classification
        m_isa = is_a_pattern.search(s)
        if m_isa:
            subject = m_isa.group(1).strip()
            predicate = m_isa.group(2).strip()
            if subject.lower() not in ["it", "this", "that", "these", "there"] and len(subject.split()) <= 4:
                candidates.append({
                    "type": "classification",
                    "subject": subject.title(),
                    "predicate": predicate,
                    "sentence": s
                })
                continue

        # General factual sentences with key terms
        if any(marker in s.lower() for marker in ["important", "primary", "mechanism", "advantage", "feature", "architecture"]):
            candidates.append({
                "type": "general_fact",
                "subject": words[0].title(),
                "predicate": " ".join(words[1:]),
                "sentence": s
            })

    return candidates


def generate_distractors(
    correct_text: str,
    all_subjects: List[str],
    domain_fallback: List[str]
) -> List[str]:
    """
    Generates 3 plausible distractors distinct from the correct option.
    Uses peer concepts from the same lecture first, then domain-related educational fallbacks.
    """
    distractors = set()
    cleaned_correct = correct_text.strip().lower()

    # Prioritize candidate subjects from the lecture
    for s in all_subjects:
        cand = s.strip()
        if cand.lower() != cleaned_correct and len(cand) > 1 and cand.lower() not in distractors:
            distractors.add(cand)
            if len(distractors) == 3:
                break

    # If still need distractors, draw from educational / CS domain bank
    for fallback in domain_fallback:
        if len(distractors) >= 3:
            break
        if fallback.lower() != cleaned_correct and fallback.lower() not in distractors:
            distractors.add(fallback)

    # Ensure exactly 3 distractors
    while len(distractors) < 3:
        placeholder = f"Alternative Concept {len(distractors) + 1}"
        distractors.add(placeholder)

    return list(distractors)[:3]


def generate_mcqs_from_text(
    transcript_text: str,
    summary_text: str,
    num_questions: int = 5,
    difficulty: str = "Medium"
) -> List[Dict[str, Any]]:
    """
    Generates multiple-choice questions grounded in the lecture.
    Ensures:
    - 4 distinct options per question
    - 1 correct answer
    - Pedagogical explanation
    - Reference context passage
    """
    corpus = f"{summary_text} {transcript_text}".strip()
    candidate_facts = extract_candidate_facts(corpus)

    # Pool of all subjects across facts for distractor mining
    all_subjects = list({f["subject"] for f in candidate_facts if len(f.get("subject", "")) > 2})

    # Domain fallbacks for computer science / deep learning / data science
    general_distractors_bank = [
        "Feature Representation", "Stochastic Gradient Descent", "Backpropagation Algorithm",
        "Convolutional Layer", "Recurrent Unit", "Transformer Attention",
        "Latent Space Embedding", "Batch Normalization", "Cross-Entropy Loss",
        "Overfitting Regularization", "Data Augmentation", "Gradient Clipping",
        "Hyperparameter Tuning", "Learning Rate Schedule", "Dropout Mechanism"
    ]

    generated_questions = []
    used_questions = set()

    for fact in candidate_facts:
        if len(generated_questions) >= num_questions:
            break

        f_type = fact["type"]
        subject = fact["subject"]
        predicate = fact["predicate"]
        sentence = fact["sentence"]

        question_text = ""
        correct_answer = ""
        explanation = ""

        if f_type == "definition":
            # Form 1: Given definition, what term is it?
            if random.random() > 0.5:
                question_text = f"Which term is defined as: '{predicate}'?"
                correct_answer = subject
                explanation = f"According to the lecture, {subject} is defined as {predicate}."
                distractors = generate_distractors(correct_answer, all_subjects, general_distractors_bank)
            else:
                # Form 2: What is the definition of subject?
                question_text = f"What is the definition or role of '{subject}' discussed in the lecture?"
                correct_answer = f"It refers to {predicate}."
                explanation = f"In the lecture context, {subject} {predicate}."
                # Build predicate-style distractors
                other_preds = [f["predicate"] for f in candidate_facts if f["subject"] != subject]
                alt_preds = other_preds[:3] if len(other_preds) >= 3 else [
                    "It acts as a linear projection without activation functions.",
                    "It stores static precomputed embeddings without backpropagation.",
                    "It minimizes inference latency by quantizing precision to 1-bit."
                ]
                distractors = [f"It refers to {p}." for p in alt_preds[:3]]

        elif f_type == "function":
            question_text = f"What is the primary function of '{subject}' as explained in the lecture?"
            correct_answer = f"To {predicate}." if not predicate.lower().startswith("to") else predicate.capitalize()
            explanation = f"As stated in the lecture: '{sentence}'"
            other_preds = [f["predicate"] for f in candidate_facts if f["subject"] != subject]
            alt_preds = other_preds[:3] if len(other_preds) >= 3 else [
                "To optimize disk storage constraints during training.",
                "To manage network socket transmission protocols.",
                "To bypass gradient calculation in evaluation mode."
            ]
            distractors = [f"To {p}." if not p.lower().startswith("to") else p.capitalize() for p in alt_preds[:3]]

        elif f_type == "classification":
            question_text = f"Based on the lecture, how is '{subject}' classified?"
            correct_answer = subject
            question_text = f"Which of the following is described as '{predicate}'?"
            explanation = f"The lecture notes highlight that {subject} is {predicate}."
            distractors = generate_distractors(correct_answer, all_subjects, general_distractors_bank)

        else:
            # General fact
            question_text = f"According to the lecture, which statement regarding '{subject}' is correct?"
            correct_answer = sentence
            explanation = f"Directly referenced from the lecture transcript: '{sentence}'"
            distractors = [
                f"{subject} is completely replaced by static rules without learning.",
                f"{subject} operates without requiring any contextual input.",
                f"{subject} produces constant outputs regardless of loss optimization."
            ]

        # Check duplicate question
        norm_q = question_text.lower().strip()
        if norm_q in used_questions or len(question_text) < 15:
            continue

        # Combine options and ensure 4 unique options
        options_set = {correct_answer}
        for d in distractors:
            if d != correct_answer and d not in options_set:
                options_set.add(d)

        while len(options_set) < 4:
            options_set.add(f"None of the other options ({len(options_set) + 1})")

        options = list(options_set)[:4]
        # Shuffle so correct answer isn't always in first slot
        random.shuffle(options)

        used_questions.add(norm_q)
        generated_questions.append({
            "id": len(generated_questions) + 1,
            "question": question_text,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "context_source": sentence
        })

    # If candidate facts yielded fewer than requested questions, create targeted comprehension questions
    if len(generated_questions) < num_questions and corpus:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", corpus) if len(s.strip().split()) >= 8]
        for s in sentences:
            if len(generated_questions) >= num_questions:
                break
            words = s.split()
            key_word = words[0].title() if len(words[0]) > 4 else (words[1].title() if len(words) > 1 else "Topic")
            q_text = f"Which statement best summarizes the following lecture insight: '{s[:80]}...'?"
            if q_text.lower() in used_questions:
                continue

            opts = [
                s,
                f"The concept of {key_word} was declared obsolete by modern research.",
                f"The lecture mentions {key_word} has no measurable effect on model performance.",
                f"{key_word} is exclusively applied in hardware circuit design."
            ]
            random.shuffle(opts)
            used_questions.add(q_text.lower())
            generated_questions.append({
                "id": len(generated_questions) + 1,
                "question": q_text,
                "options": opts,
                "correct_answer": s,
                "explanation": f"Grounded in the statement: '{s}'",
                "context_source": s
            })

    return generated_questions


def evaluate_quiz_submission(
    stored_questions: List[Dict[str, Any]],
    user_answers: List[Dict[str, Any]],
    time_taken: float = 0.0
) -> Dict[str, Any]:
    """
    Grades user submission against verified stored answers.
    Calculates score, percentage, and detailed evaluation for each question.
    """
    questions_map = {q["id"]: q for q in stored_questions}
    total_questions = len(stored_questions)
    correct_count = 0
    evaluations = []

    for item in user_answers:
        q_id = item.get("question_id")
        user_choice = item.get("selected_option", "").strip()

        q_data = questions_map.get(q_id)
        if not q_data:
            continue

        correct_choice = q_data.get("correct_answer", "").strip()
        is_correct = (user_choice == correct_choice)

        if is_correct:
            correct_count += 1

        evaluations.append({
            "question_id": q_id,
            "question": q_data.get("question"),
            "user_answer": user_choice,
            "correct_answer": correct_choice,
            "is_correct": is_correct,
            "explanation": q_data.get("explanation", ""),
            "context_source": q_data.get("context_source", "")
        })

    # Include any unattempted questions
    attempted_ids = {item.get("question_id") for item in user_answers}
    for q_id, q_data in questions_map.items():
        if q_id not in attempted_ids:
            evaluations.append({
                "question_id": q_id,
                "question": q_data.get("question"),
                "user_answer": "Not Attempted",
                "correct_answer": q_data.get("correct_answer", ""),
                "is_correct": False,
                "explanation": q_data.get("explanation", ""),
                "context_source": q_data.get("context_source", "")
            })

    # Sort evaluations by question_id
    evaluations.sort(key=lambda x: x["question_id"])

    percentage = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0.0

    return {
        "total_questions": total_questions,
        "correct_answers": correct_count,
        "score_percentage": percentage,
        "time_taken_seconds": round(time_taken, 1),
        "evaluations": evaluations
    }
