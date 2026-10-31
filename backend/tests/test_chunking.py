"""
Unit tests for transcript text cleaning, sentence segmentation, and chunking.
"""

from backend.app.services.summarization_service import (
    clean_transcript_text,
    chunk_text_by_sentences,
)


def test_clean_transcript_text():
    raw = "  Hello   world! [00:15]  This is   a test.  \n\n "
    cleaned = clean_transcript_text(raw)
    assert "[00:15]" not in cleaned
    assert "  " not in cleaned
    assert cleaned == "Hello world! This is a test."


def test_chunk_text_by_sentences_preserves_sentences():
    text = (
        "First sentence in the lecture. "
        "Second sentence discussing attention weights. "
        "Third sentence on gradient backpropagation. "
        "Fourth sentence covering transformer encoders."
    )
    chunks = chunk_text_by_sentences(text, max_chunk_words=12, overlap_sentences=1)
    assert len(chunks) > 1
    # Ensure no sentence is chopped in half
    for c in chunks:
        assert c.endswith(".")
