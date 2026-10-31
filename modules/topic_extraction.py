"""
Topic and Key Concept Extraction Module for LectureAI.
Extracts main topics, subtopics, domain keywords, definitions, formulas, and methods,
mapping concepts to transcript segment timestamps.
"""

import re
import logging
from collections import Counter
from typing import Dict, List, Tuple, Any, Optional

from modules.summarization import clean_text_for_nlp

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "in", "on", "at",
    "to", "for", "with", "about", "that", "this", "these", "those", "it", "they", "we",
    "you", "i", "he", "she", "of", "by", "as", "from", "be", "have", "has", "had",
    "do", "does", "did", "can", "could", "will", "would", "should", "so", "if", "not",
    "also", "which", "there", "then", "into", "their", "our", "my", "your", "its", "so",
    "well", "like", "just", "now", "know", "mean", "actually", "basically", "today",
    "lecture", "talk", "going", "talked", "look", "see", "here", "okay", "alright", "want",
    "think", "said", "one", "two", "first", "next", "something", "things", "thing", "way",
    "lot", "many", "much", "very", "really", "kind", "sort", "different", "use", "using"
}


def extract_keywords_tfidf(text: str, top_n: int = 15) -> List[Tuple[str, float]]:
    """
    Extract key single and bi-gram terms using TF-IDF vectorization from scikit-learn.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", clean_text_for_nlp(text))
            if len(s.strip().split()) >= 4
        ]
        if len(sentences) < 2:
            sentences = [text, text]

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_df=0.85,
            min_df=1,
            max_features=top_n * 2,
        )
        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()

        # Compute average TF-IDF score across sentences
        avg_scores = tfidf_matrix.mean(axis=0).A1
        scored_keywords = sorted(
            zip(feature_names, avg_scores), key=lambda x: x[1], reverse=True
        )

        filtered = []
        for word, score in scored_keywords:
            if word.lower() not in STOPWORDS and len(word) > 2:
                filtered.append((word.title(), round(float(score), 3)))
            if len(filtered) >= top_n:
                break
        return filtered
    except Exception as e:
        logger.debug("TF-IDF extraction fallback to frequency: %s", e)
        # Fallback to pure frequency counter
        words = [
            w.lower()
            for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)
            if w.lower() not in STOPWORDS
        ]
        counts = Counter(words).most_common(top_n)
        return [(word.title(), round(cnt / max(1, len(words)), 3)) for word, cnt in counts]


def extract_definitions_and_terms(text: str) -> List[Dict[str, str]]:
    """
    Detect explicit definition constructs such as:
    - '[Term] is defined as ...'
    - '[Term] refers to ...'
    - '[Term] is called ...'
    """
    patterns = [
        r"([A-Z][a-zA-Z\s]{2,25})\s+(?:is|are)\s+defined\s+as\s+([^.]+)",
        r"([A-Z][a-zA-Z\s]{2,25})\s+refers\s+to\s+([^.]+)",
        r"([A-Z][a-zA-Z\s]{2,25})\s+(?:is|are)\s+known\s+as\s+([^.]+)",
        r"(?:we\s+call\s+|defined\s+as\s+)([A-Z][a-zA-Z\s]{2,25})\s+([^.]+)",
    ]

    definitions = []
    seen_terms = set()

    for pat in patterns:
        matches = re.findall(pat, text)
        for term, explanation in matches:
            clean_term = term.strip()
            clean_expl = explanation.strip()
            if (
                clean_term.lower() not in seen_terms
                and len(clean_term.split()) <= 4
                and clean_term.lower() not in STOPWORDS
            ):
                definitions.append({"term": clean_term, "definition": clean_expl})
                seen_terms.add(clean_term.lower())
            if len(definitions) >= 8:
                break

    return definitions


def extract_methods_and_formulas(text: str) -> List[str]:
    """Detect formulas, algorithms, rules, or mathematical expressions mentioned."""
    findings = []
    # Pattern for equations, formulas, algorithms
    eq_regex = re.compile(
        r"(?:formula|equation|algorithm|theorem|law|method)\s*(?:for|of|is|:)?\s*([^.,;\n]{5,60})",
        re.IGNORECASE,
    )
    for m in eq_regex.finditer(text):
        match_str = m.group(0).strip()
        if match_str and len(match_str.split()) >= 3:
            findings.append(match_str)
        if len(findings) >= 5:
            break

    # Look for inline math notation like x = y, E = mc^2, or functions f(x)
    math_notations = re.findall(r"\b[A-Za-z]\s*=\s*[A-Za-z0-9\+\-\*\/\^\(\)\s]{3,20}\b", text)
    for mn in math_notations[:3]:
        findings.append(f"Expression: {mn.strip()}")

    return list(dict.fromkeys(findings))  # unique


def find_timestamp_for_concept(
    concept: str, segments: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Locate the earliest transcript segment timestamp that mentions the concept."""
    if not segments or not concept:
        return None

    concept_words = set(concept.lower().split())
    for seg in segments:
        seg_text = seg["text"].lower()
        if all(w in seg_text for w in concept_words):
            return {
                "start": seg["start"],
                "end": seg["end"],
                "text_snippet": seg["text"],
            }
    return None


def extract_topics_and_concepts(
    transcript_text: str,
    segments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Master topic extraction function.
    Returns:
        {
            "main_topics": list of dicts {topic, timestamp, segment_snippet},
            "subtopics": list of str,
            "keywords": list of {keyword, score, timestamp},
            "definitions": list of {term, definition},
            "methods_and_formulas": list of str,
            "repeated_concepts": list of {concept, count}
        }
    """
    segments = segments or []
    cleaned_text = clean_text_for_nlp(transcript_text)

    # 1. Keywords via TF-IDF
    raw_keywords = extract_keywords_tfidf(cleaned_text, top_n=15)
    keywords_with_time = []
    for kw, score in raw_keywords:
        ts_info = find_timestamp_for_concept(kw, segments)
        keywords_with_time.append(
            {
                "keyword": kw,
                "score": score,
                "timestamp": ts_info["start"] if ts_info else None,
                "snippet": ts_info["text_snippet"] if ts_info else "",
            }
        )

    # 2. Main Topics & Subtopics
    # Heuristic: top keywords + high frequency bigrams form the thematic cluster
    main_topics = []
    subtopics = []
    for item in keywords_with_time[:5]:
        main_topics.append(
            {
                "topic": item["keyword"],
                "timestamp": item["timestamp"],
                "snippet": item["snippet"],
            }
        )

    for item in keywords_with_time[5:12]:
        subtopics.append(item["keyword"])

    # 3. Repeated Concepts
    words = [
        w.lower()
        for w in re.findall(r"\b[a-zA-Z]{4,}\b", cleaned_text)
        if w.lower() not in STOPWORDS
    ]
    counts = Counter(words).most_common(8)
    repeated_concepts = [{"concept": c[0].title(), "count": c[1]} for c in counts if c[1] >= 2]

    # 4. Definitions & Terms
    definitions = extract_definitions_and_terms(cleaned_text)

    # 5. Methods & Formulas
    methods_formulas = extract_methods_and_formulas(cleaned_text)

    return {
        "main_topics": main_topics,
        "subtopics": subtopics,
        "keywords": keywords_with_time,
        "definitions": definitions,
        "methods_and_formulas": methods_formulas,
        "repeated_concepts": repeated_concepts,
    }
