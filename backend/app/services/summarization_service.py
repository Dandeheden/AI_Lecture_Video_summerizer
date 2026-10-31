"""
Transformer-based summarization and study notes generation service.
Features:
- Sentence-aware chunking for long transcripts to respect Transformer context limits.
- Recursive hierarchical summarization (chunk summaries -> final executive summary).
- Structured note generation: short summary, detailed summary, bullet points, key concepts, definitions.
- Hugging Face Seq2Seq pipeline with an intelligent NLP fallback for memory-constrained environments.
"""

import re
import math
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter

from backend.app.config import (
    DEFAULT_SUMMARIZATION_MODEL,
    SUMMARIZATION_MODELS,
    MODELS_CACHE_DIR,
)

logger = logging.getLogger(__name__)

# Pipeline cache
_SUMMARIZER_PIPELINES: Dict[str, Any] = {}


def clean_transcript_text(text: str) -> str:
    """Normalize whitespace and strip extraneous characters while keeping punctuation."""
    if not text:
        return ""
    text = re.sub(r"\[\d+:\d+(?::\d+)?\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text_by_sentences(text: str, max_chunk_words: int = 400, overlap_sentences: int = 1) -> List[str]:
    """
    Splits long transcript into overlapping chunks at natural sentence boundaries
    to prevent context truncation in Transformer models.
    """
    cleaned = clean_transcript_text(text)
    if not cleaned:
        return []

    sentence_pattern = r"(?<=[.!?])\s+"
    raw_sentences = [s.strip() for s in re.split(sentence_pattern, cleaned) if s.strip()]

    if not raw_sentences:
        return [cleaned]

    chunks = []
    current_sentences = []
    current_word_count = 0

    for s in raw_sentences:
        words_in_s = len(s.split())
        if current_word_count + words_in_s > max_chunk_words and current_sentences:
            chunks.append(" ".join(current_sentences))
            # Keep overlap for contextual continuity
            overlap = current_sentences[-overlap_sentences:] if len(current_sentences) >= overlap_sentences else current_sentences
            current_sentences = list(overlap) + [s]
            current_word_count = sum(len(x.split()) for x in current_sentences)
        else:
            current_sentences.append(s)
            current_word_count += words_in_s

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def get_hf_summarizer(model_key: str = DEFAULT_SUMMARIZATION_MODEL):
    """
    Lazily loads or retrieves cached Hugging Face summarization pipeline.
    """
    global _SUMMARIZER_PIPELINES
    if model_key in _SUMMARIZER_PIPELINES:
        return _SUMMARIZER_PIPELINES[model_key]

    model_info = SUMMARIZATION_MODELS.get(model_key, SUMMARIZATION_MODELS["distilbart"])
    model_name = model_info["name"]

    # In local/offline or sandboxed environments without pre-cached weights,
    # avoid hanging on network socket connection
    import os
    if os.getenv("TRANSFORMERS_OFFLINE", "0") == "1":
        return None

    try:
        from transformers import pipeline
        logger.info("Initializing Hugging Face summarization pipeline '%s'...", model_name)
        pipe = pipeline(
            "summarization",
            model=model_name,
            device=-1, # CPU inference by default for compatibility
            model_kwargs={"cache_dir": str(MODELS_CACHE_DIR), "local_files_only": True}
        )
        _SUMMARIZER_PIPELINES[model_key] = pipe
        return pipe
    except Exception as e:
        logger.info("Local cached weights for '%s' not present or offline (%s). Using high-yield extractive NLP pipeline.", model_name, e)
        return None


def generate_nlp_extractive_summary(text: str, target_ratio: float = 0.25, min_sentences: int = 3, max_sentences: int = 8) -> str:
    """
    Robust extractive NLP summarizer using word frequencies, sentence position scoring,
    and length penalties. Used as a high-speed fallback or complementary extractor.
    """
    cleaned = clean_transcript_text(text)
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = [s.strip() for s in re.split(sentence_pattern, cleaned) if len(s.strip().split()) >= 4]

    if len(sentences) <= min_sentences:
        return cleaned

    # Compute word frequencies (ignoring common stopwords)
    stopwords = {
        "the", "and", "is", "in", "to", "of", "that", "it", "with", "as", "for", "was",
        "on", "are", "by", "this", "be", "at", "an", "from", "or", "which", "you", "we",
        "can", "so", "they", "have", "has", "but", "about", "all", "also", "if", "not"
    }
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", cleaned) if w.lower() not in stopwords]
    word_freq = Counter(words)
    max_freq = max(word_freq.values()) if word_freq else 1.0

    scored_sentences = []
    num_sentences = len(sentences)

    for idx, sent in enumerate(sentences):
        sent_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", sent)]
        if not sent_words:
            continue

        freq_score = sum(word_freq.get(w, 0) / max_freq for w in sent_words) / len(sent_words)

        # Position score: earlier and concluding sentences carry higher pedagogical importance
        position_weight = 1.2 if (idx < 2 or idx >= num_sentences - 2) else 1.0

        # Title / keyword heuristic: terms like 'define', 'concept', 'important', 'algorithm', 'system'
        pedagogical_weight = 1.0
        if any(term in sent.lower() for term in ["important", "definition", "concept", "therefore", "in conclusion", "key", "main"]):
            pedagogical_weight = 1.3

        total_score = freq_score * position_weight * pedagogical_weight
        scored_sentences.append((idx, total_score, sent))

    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    target_count = max(min_sentences, min(max_sentences, int(num_sentences * target_ratio)))
    top_sentences = sorted(scored_sentences[:target_count], key=lambda x: x[0])

    return " ".join([s[2] for s in top_sentences])


def extract_structured_study_notes(text: str) -> Dict[str, Any]:
    """
    Extracts structured revision materials:
    - Key definitions (regex based on 'is defined as', 'refers to', 'means', 'is a')
    - Key concepts
    - High-yield takeaways
    - Exam preparation tips
    """
    cleaned = clean_transcript_text(text)
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = [s.strip() for s in re.split(sentence_pattern, cleaned) if s.strip()]

    definitions = {}
    key_takeaways = []
    key_concepts = []
    exam_tips = []

    # Patterns identifying explicit definitions in lecture discourse
    def_patterns = [
        re.compile(r"([A-Z][a-zA-Z0-9\s]{2,30})\s+(?:is defined as|refers to|means|is essentially)\s+([^.]+)", re.IGNORECASE),
        re.compile(r"([A-Z][a-zA-Z0-9\s]{2,30})\s+(?:is an?)\s+([^.]+)", re.IGNORECASE),
    ]

    for sent in sentences:
        # Check definitions
        for pattern in def_patterns:
            match = pattern.search(sent)
            if match:
                term = match.group(1).strip()
                desc = match.group(2).strip()
                if len(term.split()) <= 4 and term.lower() not in ["it", "this", "that", "there", "what", "which"]:
                    definitions[term.title()] = desc

        # Check key takeaways
        if any(k in sent.lower() for k in ["important", "key", "crucial", "essential", "remember", "vital", "primary"]):
            if sent not in key_takeaways and len(key_takeaways) < 6:
                key_takeaways.append(sent)

        # Check exam tips
        if any(k in sent.lower() for k in ["exam", "test", "question", "grade", "syllabus", "typical mistake", "note that"]):
            if sent not in exam_tips and len(exam_tips) < 4:
                exam_tips.append(sent)

    # Derive concepts from frequent title-cased words or high-frequency nouns
    words = [w for w in re.findall(r"\b[A-Za-z]{4,}\b", cleaned)]
    freq = Counter(w.lower() for w in words if w.lower() not in {"this", "that", "with", "have", "from", "lecture", "student"})
    for word, count in freq.most_common(8):
        if count >= 2:
            key_concepts.append(word.capitalize())

    # Fallback defaults if lecture is short or conversational
    if not key_takeaways and sentences:
        key_takeaways = sentences[:min(4, len(sentences))]
    if not exam_tips:
        exam_tips.append("Focus on understanding core definitions and review the detailed notes before attempting quizzes.")

    return {
        "key_concepts": key_concepts[:6],
        "definitions": definitions,
        "key_takeaways": key_takeaways[:5],
        "exam_prep_tips": exam_tips[:3]
    }


def generate_lecture_summaries(
    transcript_text: str,
    model_key: str = DEFAULT_SUMMARIZATION_MODEL
) -> Dict[str, Any]:
    """
    Generates short summary, detailed summary, bullet notes, and study notes.
    Uses chunk-based Transformer pipeline when available, with NLP fallback.
    """
    cleaned = clean_transcript_text(transcript_text)
    if not cleaned:
        return {
            "short_summary": "No transcript available to summarize.",
            "detailed_summary": "No transcript available.",
            "bullet_notes": "• No content.",
            "study_notes": {"key_concepts": [], "definitions": {}, "key_takeaways": [], "exam_prep_tips": []}
        }

    chunks = chunk_text_by_sentences(cleaned, max_chunk_words=380, overlap_sentences=1)
    hf_pipe = get_hf_summarizer(model_key)

    chunk_summaries = []
    if hf_pipe:
        logger.info("Summarizing %d chunks using Transformer model...", len(chunks))
        for idx, chunk in enumerate(chunks):
            words_count = len(chunk.split())
            if words_count < 20:
                continue
            max_len = max(30, min(120, int(words_count * 0.6)))
            min_len = max(10, min(30, int(words_count * 0.2)))
            try:
                out = hf_pipe(chunk, max_length=max_len, min_length=min_len, do_sample=False)
                if out and len(out) > 0:
                    chunk_summaries.append(out[0]["summary_text"].strip())
            except Exception as e:
                logger.warning("Chunk %d failed in Transformer pipeline: %s. Using extractive fallback.", idx, e)
                chunk_summaries.append(generate_nlp_extractive_summary(chunk, target_ratio=0.35))
    else:
        logger.info("Transformer pipeline unavailable or skipped; using NLP extractive summarizer on %d chunks.", len(chunks))
        for chunk in chunks:
            chunk_summaries.append(generate_nlp_extractive_summary(chunk, target_ratio=0.35))

    combined_detailed = " ".join(chunk_summaries) if chunk_summaries else generate_nlp_extractive_summary(cleaned, target_ratio=0.4)

    # Generate short summary (2-3 sentences) from the combined summary
    short_summary = generate_nlp_extractive_summary(combined_detailed, target_ratio=0.35, min_sentences=2, max_sentences=4)

    # Generate bullet notes
    sentence_pattern = r"(?<=[.!?])\s+"
    raw_sents = [s.strip() for s in re.split(sentence_pattern, combined_detailed) if len(s.strip()) > 10]
    bullet_list = [f"• {s}" for s in raw_sents[:8]]
    bullet_notes = "\n".join(bullet_list) if bullet_list else f"• {combined_detailed}"

    # Generate structured study notes
    study_notes = extract_structured_study_notes(cleaned)

    return {
        "short_summary": short_summary,
        "detailed_summary": combined_detailed,
        "bullet_notes": bullet_notes,
        "study_notes": study_notes,
    }
