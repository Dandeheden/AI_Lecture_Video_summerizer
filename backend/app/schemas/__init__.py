from backend.app.schemas.lecture_schemas import (
    LectureUploadResponse,
    LectureStatusResponse,
    LectureTranscriptResponse,
    LectureSummaryResponse,
    LectureNotesResponse,
    LectureHistoryResponse,
    LectureHistoryItem,
    TranscriptSegment,
    StudyNotes,
    TopicExtractionResult,
)
from backend.app.schemas.quiz_schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizQuestionItem,
    QuestionGradingResult,
)

__all__ = [
    "LectureUploadResponse",
    "LectureStatusResponse",
    "LectureTranscriptResponse",
    "LectureSummaryResponse",
    "LectureNotesResponse",
    "LectureHistoryResponse",
    "LectureHistoryItem",
    "TranscriptSegment",
    "StudyNotes",
    "TopicExtractionResult",
    "QuizGenerateRequest",
    "QuizResponse",
    "QuizSubmitRequest",
    "QuizResultResponse",
    "QuizQuestionItem",
    "QuestionGradingResult",
]
