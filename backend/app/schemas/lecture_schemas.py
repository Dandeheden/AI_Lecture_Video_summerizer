"""
Pydantic schemas for Lecture endpoints and data contracts.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Recognized speech text")


class LectureUploadResponse(BaseModel):
    id: int
    title: str
    original_filename: str
    file_type: str
    file_size_mb: float
    status: str
    message: str


class LectureStatusResponse(BaseModel):
    id: int
    title: str
    status: str
    progress_percent: int
    status_message: str
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    detected_language: str = "en"
    updated_at: datetime


class LectureTranscriptResponse(BaseModel):
    lecture_id: int
    title: str
    detected_language: str
    duration_seconds: float
    transcript_text: str
    segments: List[TranscriptSegment]


class StudyNotes(BaseModel):
    key_concepts: List[str] = []
    definitions: Dict[str, str] = {}
    key_takeaways: List[str] = []
    exam_prep_tips: List[str] = []


class TopicExtractionResult(BaseModel):
    main_topics: List[str] = []
    subtopics: List[str] = []
    keywords: List[str] = []


class LectureSummaryResponse(BaseModel):
    lecture_id: int
    title: str
    short_summary: str
    detailed_summary: str
    bullet_notes: str
    topics: TopicExtractionResult


class LectureNotesResponse(BaseModel):
    lecture_id: int
    title: str
    study_notes: StudyNotes
    bullet_notes: str


class LectureHistoryItem(BaseModel):
    id: int
    title: str
    original_filename: str
    file_type: str
    file_size_mb: float
    duration_seconds: float
    detected_language: str
    status: str
    progress_percent: int
    has_transcript: bool
    has_summary: bool
    has_quiz: bool
    created_at: datetime
    updated_at: datetime


class LectureHistoryResponse(BaseModel):
    total_lectures: int
    lectures: List[LectureHistoryItem]
