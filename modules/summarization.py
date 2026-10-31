"""
AI Summarization and Study Notes Module for LectureAI.
Uses Hugging Face Transformers (FLAN-T5 / BART) with chunking for long transcripts,
and an intelligent NLP fallback when transformer weights are unavailable or memory-limited.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from config import (
    DEFAULT_SUMMARIZATION_MODEL,
    SUMMARIZATION_MODELS,
    SUMMARY_LENGTH_CONFIG,
    MODELS_CACHE_DIR,
)

logger = logging.getLogger(__name__)

# Cache pipeline across Streamlit calls
_LOADED_SUMMARIZERS = {}


def clean_text_for_nlp(text: str) -> str:
    """Standardize whitespace and strip unprintable characters."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[\d+:\d+(?::\d+)?\]", "", text)  # remove inline timestamps if any
    return text.strip()


def split_text_into_chunks(text: str, max_chunk_words: int = 450) -> List[str]:
    """
    Split text into semantically cohesive chunks by sentence boundaries,
    ensuring each chunk fits within Transformer context windows.
    """
    cleaned = clean_text_for_nlp(text)
    if not cleaned:
        return []

    # Split into sentences using regex
    sentence_pattern = r"(?<=[.!?])\s+"
    raw_sentences = re.split(sentence_pattern, cleaned)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_word_count = 0

    for s in sentences:
        words = s.split()
        num_words = len(words)
        if current_word_count + num_words > max_chunk_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [s]
            current_word_count = num_words
        else:
            current_chunk.append(s)
            current_word_count += num_words

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def get_summarizer_pipeline(model_key: str = DEFAULT_SUMMARIZATION_MODEL):
    """
    Load or retrieve a cached Hugging Face summarization pipeline.
    """
    from transformers import pipeline

    if model_key in _LOADED_SUMMARIZERS:
        return _LOADED_SUMMARIZERS[model_key]

    model_config = SUMMARIZATION_MODELS.get(
        model_key, SUMMARIZATION_MODELS[DEFAULT_SUMMARIZATION_MODEL]
    )
    model_name = model_config["name"]

    logger.info("Initializing Hugging Face pipeline for '%s'...", model_name)
    try:
        pipe = pipeline(
            "summarization",
            model=model_name,
            tokenizer=model_name,
            device=-1,  # CPU by default for stability
            model_kwargs={"cache_dir": str(MODELS_CACHE_DIR)},
        )
        _LOADED_SUMMARIZERS[model_key] = pipe
        return pipe
    except Exception as e:
        logger.warning(
            "Hugging Face model '%s' could not be loaded directly (%s).",
            model_name,
            e,
        )
        return None


def generate_extractive_summary(text: str, target_sentence_count: int = 5) -> List[str]:
    """
    NLP-based sentence-scoring extractive summarizer (TextRank / TF-IDF style).
    Used directly or as high-speed reliable fallback when transformer weights are not yet cached.
    """
    from collections import Counter
    import math

    cleaned = clean_text_for_nlp(text)
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", cleaned)
        if len(s.strip().split()) >= 4
    ]

    if not sentences:
        return [text]

    if len(sentences) <= target_sentence_count:
        return sentences

    # Calculate word frequencies (ignoring common stopwords)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "in", "on", "at",
        "to", "for", "with", "about", "that", "this", "these", "those", "it", "they", "we",
        "you", "i", "he", "she", "of", "by", "as", "from", "be", "have", "has", "had",
        "do", "does", "did", "can", "could", "will", "would", "should", "so", "if", "not",
        "also", "which", "there", "then", "into", "their", "our", "my", "your", "its", "so",
        "well", "like", "just", "now", "know", "mean", "actually", "basically", "today",
        "lecture", "talk", "going", "talked", "look", "see", "here", "okay", "alright"
    }

    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", cleaned) if w.lower() not in stopwords]
    word_freq = Counter(words)
    max_freq = max(word_freq.values()) if word_freq else 1

    # Sentence scoring
    sentence_scores = []
    for idx, sentence in enumerate(sentences):
        sent_words = [
            w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", sentence) if w.lower() not in stopwords
        ]
        if not sent_words:
            sentence_scores.append((idx, 0.0, sentence))
            continue

        raw_score = sum(word_freq[w] / max_freq for w in sent_words)
        # Length normalization
        score = raw_score / (len(sent_words) ** 0.5)

        # Boost sentences containing key indicator phrases
        indicators = ["important", "definition", "concept", "conclusion", "key", "result", "principle", "therefore", "fundamental"]
        for ind in indicators:
            if ind in sentence.lower():
                score *= 1.25

        # Slight boost to first 15% and last 15% of the lecture (intro & conclusion bias)
        pos_ratio = idx / max(1, len(sentences) - 1)
        if pos_ratio < 0.15 or pos_ratio > 0.85:
            score *= 1.15

        sentence_scores.append((idx, score, sentence))

    # Pick top sentences while preserving chronological flow
    top_scored = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:target_sentence_count]
    top_chronological = sorted(top_scored, key=lambda x: x[0])
    return [s[2] for s in top_chronological]


def generate_lecture_summaries(
    transcript_text: str,
    model_key: str = DEFAULT_SUMMARIZATION_MODEL,
    length_preset: str = "Medium",
    style_preset: str = "Paragraphs",
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Main summarization pipeline.
    Produces:
        - short_summary
        - detailed_summary
        - bullet_notes
        - structured_study_notes (dict of sections)
        - engine_used (Transformer name or Extractive NLP Engine)
    """
    if not transcript_text or len(transcript_text.strip().split()) < 10:
        raise ValueError("Transcript is too short to generate a meaningful summary.")

    if progress_callback:
        progress_callback(10, "Analyzing lecture transcript and building semantic chunks...")

    chunks = split_text_into_chunks(transcript_text, max_chunk_words=450)
    summarizer = get_summarizer_pipeline(model_key)

    total_words = len(transcript_text.split())
    target_config = SUMMARY_LENGTH_CONFIG.get(length_preset, SUMMARY_LENGTH_CONFIG["Medium"])

    short_summary = ""
    detailed_summary = ""
    engine_name = "Extractive NLP Engine (Rule & Frequency Based)"

    # 1. Attempt Hugging Face Transformer pipeline
    if summarizer is not None:
        try:
            if progress_callback:
                progress_callback(30, f"Running Transformer summarization ({model_key})...")

            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                chunk_len = len(chunk.split())
                max_len = min(120, max(30, int(chunk_len * 0.4)))
                min_len = min(25, max(10, int(chunk_len * 0.15)))

                res = summarizer(
                    chunk,
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False,
                    truncation=True,
                )
                chunk_summaries.append(res[0]["summary_text"])

                if progress_callback:
                    pct = 30 + int(((i + 1) / len(chunks)) * 40)
                    progress_callback(pct, f"Summarizing segment {i+1} of {len(chunks)}...")

            combined_chunk_summary = " ".join(chunk_summaries)

            # If combined summary is still long and we want short, run second pass
            if len(combined_chunk_summary.split()) > 180 and length_preset in ["Short", "Medium"]:
                try:
                    res_second = summarizer(
                        combined_chunk_summary,
                        max_length=target_config["max_words"],
                        min_length=target_config["min_words"],
                        do_sample=False,
                        truncation=True,
                    )
                    short_summary = res_second[0]["summary_text"]
                except Exception:
                    short_summary = " ".join(combined_chunk_summary.split()[: target_config["max_words"]])
            else:
                short_summary = combined_chunk_summary

            detailed_summary = combined_chunk_summary
            engine_name = f"Hugging Face Transformer ({SUMMARIZATION_MODELS[model_key]['name']})"
        except Exception as e:
            logger.warning("Transformer generation encountered an issue (%s). Using extractive engine.", e)
            summarizer = None

    # 2. Extractive NLP Fallback if Transformer unavailable or failed
    if summarizer is None:
        if progress_callback:
            progress_callback(40, "Synthesizing extractive summaries using NLP graph scoring...")

        short_sents = generate_extractive_summary(transcript_text, target_sentence_count=4)
        medium_sents = generate_extractive_summary(transcript_text, target_sentence_count=8)
        detailed_sents = generate_extractive_summary(transcript_text, target_sentence_count=14)

        short_summary = " ".join(short_sents)
        if length_preset == "Short":
            detailed_summary = " ".join(medium_sents)
        elif length_preset == "Medium":
            detailed_summary = " ".join(medium_sents)
        else:
            detailed_summary = " ".join(detailed_sents)

    if progress_callback:
        progress_callback(80, "Generating structured study notes and conceptual breakdown...")

    # Build bullet notes
    bullet_sentences = generate_extractive_summary(detailed_summary or transcript_text, target_sentence_count=6)
    bullet_notes = "\n".join([f"• {s.strip()}" for s in bullet_sentences])

    # Build Structured Study Notes
    study_notes = extract_structured_study_notes(transcript_text, detailed_summary)

    if progress_callback:
        progress_callback(100, "Summaries and study notes ready!")

    return {
        "short_summary": short_summary,
        "detailed_summary": detailed_summary,
        "bullet_notes": bullet_notes,
        "study_notes": study_notes,
        "engine_used": engine_name,
        "original_word_count": total_words,
        "summary_word_count": len(detailed_summary.split()),
        "compression_ratio": round(len(detailed_summary.split()) / max(1, total_words) * 100, 1),
    }


def extract_structured_study_notes(transcript_text: str, summary_text: str) -> Dict[str, Any]:
    """
    Generate deep, well-categorized study notes from the lecture:
    - Main Ideas & Core Thesis
    - Key Definitions & Conceptual Terms
    - Important Supporting Evidence / Points
    - Common Pitfalls & Key Takeaways
    - Rapid Revision Checklist
    """
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", clean_text_for_nlp(transcript_text))
        if len(s.strip().split()) >= 4
    ]

    # 1. Main ideas
    main_ideas = generate_extractive_summary(summary_text or transcript_text, target_sentence_count=3)

    # 2. Definitions and technical terms
    definitions = []
    def_regex = re.compile(
        r"(?:(?:is|are|was|were)\s+defined\s+as|refers\s+to|means\s+that|is\s+known\s+as|is\s+called|represents)\s+([^.]+)",
        re.IGNORECASE,
    )

    for s in sentences:
        match = def_regex.search(s)
        if match and len(s.split()) < 40:
            definitions.append(s)
            if len(definitions) >= 5:
                break

    if not definitions:
        # Fallback to key concept sentences
        definitions = [
            s for s in sentences if any(k in s.lower() for k in ["concept", "principle", "property", "rule", "model"])
        ][:4]

    # 3. Supporting points & methodology
    supporting_points = [
        s for s in sentences if any(k in s.lower() for k in ["because", "specifically", "for example", "furthermore", "approach", "method", "shows"])
    ][:5]
    if not supporting_points:
        supporting_points = generate_extractive_summary(transcript_text, target_sentence_count=4)

    # 4. Key Takeaways
    takeaways = [
        s for s in sentences if any(k in s.lower() for k in ["important", "remember", "essential", "crucial", "must", "note that", "conclude"])
    ][:4]
    if not takeaways:
        takeaways = generate_extractive_summary(transcript_text, target_sentence_count=3)

    # 5. Rapid Revision Checklist
    checklist = [
        f"Understand the core premise: {main_ideas[0] if main_ideas else 'Key lecture thesis'}",
        f"Review central definitions ({len(definitions)} identified in lecture)",
        f"Analyze relationships between key variables and core concepts",
        f"Verify practical implications and test takeaways with self-quizzing",
    ]

    return {
        "main_ideas": main_ideas,
        "definitions": definitions,
        "supporting_points": supporting_points,
        "takeaways": takeaways,
        "revision_checklist": checklist,
    }
