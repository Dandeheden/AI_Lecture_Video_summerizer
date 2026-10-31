-- Database schema for LectureAI

CREATE TABLE IF NOT EXISTS lectures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_mb REAL DEFAULT 0.0,
    duration_seconds REAL DEFAULT 0.0,
    detected_language TEXT DEFAULT 'en',
    transcript_text TEXT NOT NULL,
    transcript_segments_json TEXT, -- List of {start, end, text}
    short_summary TEXT,
    detailed_summary TEXT,
    bullet_notes TEXT,
    study_notes_json TEXT, -- Main ideas, concepts, definitions, takeaways
    topics_json TEXT, -- Extracted topics, subtopics, keywords, terms
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    question_count INTEGER NOT NULL,
    difficulty_level TEXT NOT NULL,
    questions_json TEXT NOT NULL, -- Array of question objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    lecture_id INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    score_percentage REAL NOT NULL,
    answers_json TEXT NOT NULL, -- User selections and results
    time_taken_seconds REAL DEFAULT 0.0,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_lectures_created_at ON lectures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quizzes_lecture_id ON quizzes(lecture_id);
CREATE INDEX IF NOT EXISTS idx_attempts_lecture_id ON quiz_attempts(lecture_id);
