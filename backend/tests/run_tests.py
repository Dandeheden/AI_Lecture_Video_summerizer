"""
Stand-alone test runner using Python standard library unittest.
Requires zero external test packages and verifies all core components:
- File and limit validations
- Text cleaning and sentence-aware chunking
- Summarization, key takeaways, and definitions
- MCQ synthesis with 4 distinct options and server-side grading
- Route handlers, database persistence, and system diagnostics
"""

import sys
import unittest
from pathlib import Path

# Setup sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import test cases
from backend.tests.test_validation import (
    test_supported_extensions,
    test_max_upload_size_configured,
)
from backend.tests.test_chunking import (
    test_clean_transcript_text,
    test_chunk_text_by_sentences_preserves_sentences,
)
from backend.tests.test_summarization import (
    test_extractive_summary_length_reduction,
    test_structured_notes_extraction,
)
from backend.tests.test_quiz_evaluation import (
    test_mcq_generation_options_and_structure,
    test_server_side_quiz_grading,
)
from backend.tests.test_api_endpoints import (
    test_root_endpoint,
    test_health_endpoint,
    test_history_and_stats_endpoints,
    test_database_lecture_persistence,
)


class TestLectureAISuite(unittest.TestCase):
    def test_01_validation(self):
        test_supported_extensions()
        test_max_upload_size_configured()

    def test_02_chunking(self):
        test_clean_transcript_text()
        test_chunk_text_by_sentences_preserves_sentences()

    def test_03_summarization(self):
        test_extractive_summary_length_reduction()
        test_structured_notes_extraction()

    def test_04_quiz_evaluation(self):
        test_mcq_generation_options_and_structure()
        test_server_side_quiz_grading()

    def test_05_api_and_database(self):
        test_root_endpoint()
        test_health_endpoint()
        test_history_and_stats_endpoints()
        test_database_lecture_persistence()


if __name__ == "__main__":
    print("=" * 60)
    print("Running LectureAI Automated Verification Test Suite")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLectureAISuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
