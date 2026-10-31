"""
Topic and keyword extraction service for LectureAI.
Uses TF-IDF vectorization and linguistic pattern matching to identify key concepts and subtopics.
"""

import re
import logging
from typing import Dict, List, Any
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def extract_lecture_topics(text: str, max_topics: int = 5, max_keywords: int = 10) -> Dict[str, Any]:
    """
    Extracts high-level topics, subtopics, and key terminology from the lecture transcript.
    """
    if not text or len(text.strip().split()) < 10:
        return {
            "main_topics": ["General Lecture Content"],
            "subtopics": [],
            "keywords": []
        }

    # Split text into sentence paragraphs
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = [s.strip() for s in re.split(sentence_pattern, text) if len(s.strip().split()) >= 4]

    # Stopwords list
    custom_stopwords = [
        "the", "and", "is", "in", "to", "of", "that", "it", "with", "as", "for", "was",
        "on", "are", "by", "this", "be", "at", "an", "from", "or", "which", "you", "we",
        "can", "so", "they", "have", "has", "but", "about", "all", "also", "if", "not",
        "like", "just", "going", "know", "think", "let", "see", "now", "here", "today",
        "talk", "lecture", "student", "class", "course", "slide", "next"
    ]

    # Extract 1-3 gram noun phrases and TF-IDF keywords
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=custom_stopwords,
            max_features=25,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(sentences if len(sentences) > 2 else [text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1
        top_indices = scores.argsort()[::-1]

        ranked_terms = [feature_names[i].title() for i in top_indices if len(feature_names[i]) > 3]
    except Exception as e:
        logger.warning("TF-IDF extraction failed: %s; using frequency fallback.", e)
        words = [w.title() for w in re.findall(r"\b[A-Za-z]{4,}\b", text) if w.lower() not in custom_stopwords]
        ranked_terms = [item[0] for item in Counter(words).most_common(15)]

    # Deduplicate and separate into main topics and keywords
    deduped = []
    for term in ranked_terms:
        if not any(term.lower() in d.lower() or d.lower() in term.lower() for d in deduped):
            deduped.append(term)

    main_topics = deduped[:max_topics] if deduped else ["Overview"]
    keywords = [t for t in ranked_terms if t not in main_topics][:max_keywords]

    # Derive subtopics from sentence clauses containing main topics
    subtopics = []
    for topic in main_topics[:3]:
        for s in sentences:
            if topic.lower() in s.lower() and 20 < len(s) < 120:
                clean_s = s.rstrip(".")
                if clean_s not in subtopics and len(subtopics) < 5:
                    subtopics.append(clean_s)
                break

    return {
        "main_topics": main_topics,
        "subtopics": subtopics,
        "keywords": keywords,
    }
