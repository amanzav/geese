-- Geese Database Schema - SQLite database for WaterlooWorks job automation

-- JOBS TABLE - Stores all scraped job postings from WaterlooWorks
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    division TEXT,
    location TEXT,
    level TEXT,
    openings INTEGER DEFAULT 0,
    applications INTEGER DEFAULT 0,
    chances REAL,
    deadline TEXT,
    summary TEXT,
    responsibilities TEXT,
    skills TEXT,
    additional_info TEXT,
    employment_location_arrangement TEXT,
    work_term_duration TEXT,
    application_documents_required TEXT,
    targeted_degrees_disciplines TEXT,
    compensation_value REAL,
    compensation_currency TEXT,
    compensation_period TEXT,
    compensation_raw TEXT,
    scraped_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE(job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON jobs(deadline);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);

-- JOB MATCHES TABLE - Stores AI analysis results for resume-job matching
CREATE TABLE IF NOT EXISTS job_matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    match_score REAL NOT NULL,
    decision TEXT NOT NULL,
    semantic_score REAL,
    keyword_score REAL,
    compensation_score REAL,
    experience_score REAL,
    location_score REAL,
    matched_skills TEXT,
    missing_skills TEXT,
    strengths TEXT,
    concerns TEXT,
    ai_reasoning TEXT,
    technologies TEXT,
    analyzed_at TEXT NOT NULL,
    analysis_version TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_matches_job_id ON job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_matches_decision ON job_matches(decision);
CREATE INDEX IF NOT EXISTS idx_matches_score ON job_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_matches_analyzed_at ON job_matches(analyzed_at);

-- ANALYSIS RUNS TABLE - Tracks batch analysis sessions
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,
    total_jobs INTEGER NOT NULL,
    jobs_analyzed INTEGER NOT NULL,
    jobs_applied INTEGER DEFAULT 0,
    jobs_skipped INTEGER DEFAULT 0,
    avg_match_score REAL,
    top_match_score REAL,
    execution_time_seconds REAL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    config_snapshot TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON analysis_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_mode ON analysis_runs(mode);

-- COVER LETTERS TABLE - Stores generated cover letters for job applications
CREATE TABLE IF NOT EXISTS cover_letters (
    letter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT,
    generated_at TEXT NOT NULL,
    generation_provider TEXT,
    generation_prompt TEXT,
    is_uploaded BOOLEAN DEFAULT 0,
    uploaded_at TEXT,
    word_count INTEGER,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_letters_job_id ON cover_letters(job_id);
CREATE INDEX IF NOT EXISTS idx_letters_uploaded ON cover_letters(is_uploaded);

-- APPLICATIONS TABLE - Tracks application submissions and status
CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    letter_id INTEGER,
    status TEXT DEFAULT 'draft',
    applied_at TEXT,
    documents_uploaded TEXT,
    questions_answered TEXT,
    last_status_check TEXT,
    status_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (letter_id) REFERENCES cover_letters(letter_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_applied_at ON applications(applied_at);

-- SAVED FOLDERS TABLE - Tracks which WaterlooWorks folders jobs have been saved to
CREATE TABLE IF NOT EXISTS saved_folders (
    save_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    folder_name TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    UNIQUE(job_id, folder_name)
);

CREATE INDEX IF NOT EXISTS idx_saved_job_id ON saved_folders(job_id);
CREATE INDEX IF NOT EXISTS idx_saved_folder ON saved_folders(folder_name);

-- CACHE METADATA TABLE - Stores metadata about caching state
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key TEXT PRIMARY KEY,
    cache_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- VIEWS FOR COMMON QUERIES
CREATE VIEW IF NOT EXISTS jobs_with_matches AS
SELECT 
    j.*,
    m.match_score,
    m.decision,
    m.semantic_score,
    m.ai_reasoning,
    m.matched_skills,
    m.technologies,
    m.analyzed_at
FROM jobs j
LEFT JOIN job_matches m ON j.job_id = m.job_id;

CREATE VIEW IF NOT EXISTS top_matches AS
SELECT 
    j.job_id,
    j.title,
    j.company,
    j.location,
    j.deadline,
    j.openings,
    j.applications,
    j.chances,
    m.match_score,
    m.decision,
    m.ai_reasoning,
    m.analyzed_at
FROM jobs j
INNER JOIN job_matches m ON j.job_id = m.job_id
WHERE m.decision = 'apply'
ORDER BY m.match_score DESC;

CREATE VIEW IF NOT EXISTS application_pipeline AS
SELECT 
    j.job_id,
    j.title,
    j.company,
    j.deadline,
    m.match_score,
    cl.letter_id,
    cl.is_uploaded AS cover_letter_uploaded,
    a.status AS application_status,
    a.applied_at
FROM jobs j
INNER JOIN job_matches m ON j.job_id = m.job_id
LEFT JOIN cover_letters cl ON j.job_id = cl.job_id
LEFT JOIN applications a ON j.job_id = a.job_id
WHERE m.decision = 'apply'
ORDER BY m.match_score DESC;
