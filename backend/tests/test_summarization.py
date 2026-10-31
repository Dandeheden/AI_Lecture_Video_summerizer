"""
Unit tests for summarization generation, structured notes, and glossary extraction.
"""

from backend.app.services.summarization_service import (
    generate_nlp_extractive_summary,
    extract_structured_study_notes,
    generate_lecture_summaries,
)


def test_extractive_summary_length_reduction():
    lecture = (
        "Neural networks are computational models inspired by biological nervous systems. "
        "A perceptron is the simplest form of artificial neural network used for classification. "
        "During forward propagation, inputs are multiplied by synaptic weights and summed with a bias. "
        "An activation function introduces non-linearity to enable the network to learn complex patterns. "
        "Backpropagation is essentially the reverse mode automatic differentiation algorithm used to calculate gradients. "
        "The learning rate dictates the step size taken during gradient descent optimization. "
        "Therefore, hyperparameter tuning is critical for achieving optimal model convergence and preventing overfitting."
    )
    summary = generate_nlp_extractive_summary(lecture, target_ratio=0.35, min_sentences=2, max_sentences=3)
    assert len(summary) > 0
    assert len(summary) < len(lecture)


def test_structured_notes_extraction():
    lecture = (
        "Supervised Learning is defined as learning a function that maps an input to an output based on example input-output pairs. "
        "A Loss Function refers to a mathematical measure of model inaccuracy. "
        "It is crucial to remember that validation loss must be monitored closely to detect early overfitting. "
        "For the exam, remember to review the cross-entropy formula."
    )
    notes = extract_structured_study_notes(lecture)
    assert "Supervised Learning" in notes["definitions"]
    assert len(notes["key_takeaways"]) > 0
    assert len(notes["exam_prep_tips"]) > 0
