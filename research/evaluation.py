"""
Research Evaluation Metrics Module for LectureAI.
Provides exact mathematical implementations of:
- Word Error Rate (WER) via Levenshtein dynamic programming on word sequences
- ROUGE-1, ROUGE-2, ROUGE-L (Precision, Recall, F1) via Longest Common Subsequence (LCS)
- Question Generation Metrics: Groundedness, Distractor Uniqueness, Duplicate Rate
"""

import re
import time
from typing import Dict, List, Tuple, Any, Set


def tokenize_words(text: str) -> List[str]:
    """Clean and tokenize string into lowercase alphanumeric words."""
    return re.findall(r"\b\w+\b", text.lower())


def compute_word_error_rate(reference: str, hypothesis: str) -> float:
    """
    Computes Word Error Rate (WER) = (Substitutions + Deletions + Insertions) / N
    using Wagner-Fischer dynamic programming algorithm.
    """
    ref_words = tokenize_words(reference)
    hyp_words = tokenize_words(hypothesis)

    n = len(ref_words)
    m = len(hyp_words)

    if n == 0:
        return 0.0 if m == 0 else 1.0

    # DP table: (n+1) x (m+1)
    d = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    wer = d[n][m] / float(n)
    return round(min(wer, 1.0), 4)


def get_ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """Generates contiguous token tuples of length n."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def compute_rouge_n(hypothesis: str, reference: str, n: int = 1) -> Dict[str, float]:
    """
    Computes ROUGE-N (Recall, Precision, F1-score) based on n-gram overlap.
    """
    hyp_tokens = tokenize_words(hypothesis)
    ref_tokens = tokenize_words(reference)

    hyp_ngrams = get_ngrams(hyp_tokens, n)
    ref_ngrams = get_ngrams(ref_tokens, n)

    if not ref_ngrams or not hyp_ngrams:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    ref_counts: Dict[Tuple[str, ...], int] = {}
    for g in ref_ngrams:
        ref_counts[g] = ref_counts.get(g, 0) + 1

    overlap = 0
    hyp_counts: Dict[Tuple[str, ...], int] = {}
    for g in hyp_ngrams:
        hyp_counts[g] = hyp_counts.get(g, 0) + 1

    for g, count in hyp_counts.items():
        if g in ref_counts:
            overlap += min(count, ref_counts[g])

    precision = overlap / float(len(hyp_ngrams))
    recall = overlap / float(len(ref_ngrams))
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def compute_lcs(x: List[str], y: List[str]) -> int:
    """Computes the length of Longest Common Subsequence between two token sequences."""
    n, m = len(x), len(y)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


def compute_rouge_l(hypothesis: str, reference: str) -> Dict[str, float]:
    """
    Computes ROUGE-L based on Longest Common Subsequence.
    """
    hyp_tokens = tokenize_words(hypothesis)
    ref_tokens = tokenize_words(reference)

    if not hyp_tokens or not ref_tokens:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    lcs_len = compute_lcs(hyp_tokens, ref_tokens)
    precision = lcs_len / float(len(hyp_tokens))
    recall = lcs_len / float(len(ref_tokens))
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_question_generation(questions: List[Dict[str, Any]], transcript: str) -> Dict[str, Any]:
    """
    Evaluates generated questions on:
    - 4 distinct options guarantee rate
    - Duplicate question rate
    - Grounded factual consistency (reference quote in transcript)
    """
    total_q = len(questions)
    if total_q == 0:
        return {
            "total_questions": 0,
            "distinct_options_rate": 0.0,
            "duplicate_question_rate": 0.0,
            "grounded_consistency_rate": 0.0,
        }

    valid_options_count = 0
    grounded_count = 0
    seen_questions = set()
    duplicates = 0

    norm_transcript = transcript.lower()

    for q in questions:
        # Check uniqueness of question text
        q_text = q.get("question", "").strip().lower()
        if q_text in seen_questions:
            duplicates += 1
        else:
            seen_questions.add(q_text)

        # Check options: exactly 4 unique choices
        opts = q.get("options", [])
        if len(opts) == 4 and len(set(opts)) == 4:
            valid_options_count += 1

        # Check grounded context
        ctx = q.get("context_source", "").strip()
        ans = q.get("correct_answer", "").strip()
        if (ctx and ctx.lower() in norm_transcript) or (ans and ans.lower() in norm_transcript):
            grounded_count += 1

    return {
        "total_questions": total_q,
        "distinct_options_rate": round(valid_options_count / total_q, 4),
        "duplicate_question_rate": round(duplicates / total_q, 4),
        "grounded_consistency_rate": round(grounded_count / total_q, 4),
    }
