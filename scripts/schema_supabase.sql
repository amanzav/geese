-- ============================================================================
-- SUPABASE SCHEMA - Shared Job Data (Cloud)
-- All WaterlooWorks jobs - read by all users, written by scraper
-- Cost optimization: Stores all job data centrally, users only store job_id references
-- ============================================================================

-- JOBS TABLE - Master list of all WaterlooWorks job postings
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary identification
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    division TEXT,
    location TEXT,
    level TEXT,
    
    -- Application statistics
    openings INTEGER DEFAULT 0,
    applications INTEGER DEFAULT 0,
    chances REAL,  -- Competition ratio or acceptance rate
    deadline TIMESTAMP,
    
    -- Job description details (main content sections)
    summary TEXT,
    responsibilities TEXT,
    skills TEXT,
    additional_info TEXT,
    
    -- Work arrangement details
    employment_location_arrangement TEXT,  -- e.g., "Remote", "In-person", "Hybrid"
    work_term_duration TEXT,              -- e.g., "4 months", "8 months"
    
    -- Application requirements (stored as JSONB for flexible querying)
    application_documents_required JSONB,  -- e.g., ["Resume", "Cover Letter", "Transcript"]
    targeted_degrees_disciplines JSONB,    -- e.g., ["ENG - Software Engineering", "MATH - Computer Science"]
    
    -- Compensation details
    compensation_value REAL,           -- Numeric value (e.g., 25.50)
    compensation_currency TEXT,        -- e.g., "CAD", "USD"
    compensation_period TEXT,          -- e.g., "per hour", "per month"
    compensation_raw TEXT,             -- Original text (e.g., "$25.50/hour")
    
    -- Metadata and tracking
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Full-text search (for efficient text searching)
    search_vector TSVECTOR
);

-- ============================================================================
-- INDEXES - Optimize common query patterns
-- ============================================================================

-- Standard B-tree indexes for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_level ON jobs(level);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON jobs(deadline);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active) WHERE is_active = TRUE;

-- Compensation range queries
CREATE INDEX IF NOT EXISTS idx_jobs_compensation ON jobs(compensation_value) WHERE compensation_value IS NOT NULL;

-- GIN indexes for JSONB array searches
CREATE INDEX IF NOT EXISTS idx_jobs_app_docs ON jobs USING GIN (application_documents_required);
CREATE INDEX IF NOT EXISTS idx_jobs_degrees ON jobs USING GIN (targeted_degrees_disciplines);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on jobs table
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public read access (anyone can view jobs)
CREATE POLICY "Public read access" ON jobs
    FOR SELECT 
    USING (true);

-- Policy: Only authenticated service can write (scraper/admin only)
CREATE POLICY "Service role write access" ON jobs
    FOR ALL 
    USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR 
        auth.jwt() ->> 'role' = 'authenticated'
    );

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to automatically update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the update function before any update
CREATE TRIGGER update_jobs_updated_at 
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update the search_vector for full-text search
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.company, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.skills, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.responsibilities, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update search_vector before insert or update
CREATE TRIGGER update_jobs_search_vector
    BEFORE INSERT OR UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Full-text search index (created after trigger is set up)
CREATE INDEX IF NOT EXISTS idx_jobs_search ON jobs USING GIN (search_vector);

-- ============================================================================
-- EXAMPLE QUERIES - Common use cases
-- ============================================================================

-- 1. Find all active jobs from a specific company:
-- SELECT * FROM jobs 
-- WHERE company ILIKE '%Google%' 
-- AND is_active = TRUE;

-- 2. Find jobs that require a specific document:
-- SELECT job_id, title, company, application_documents_required
-- FROM jobs 
-- WHERE application_documents_required @> '["Cover Letter"]'::jsonb;

-- 3. Find jobs targeting specific degrees:
-- SELECT job_id, title, company, targeted_degrees_disciplines
-- FROM jobs 
-- WHERE targeted_degrees_disciplines @> '["MATH - Computer Science"]'::jsonb;

-- 4. Find jobs with compensation above a threshold:
-- SELECT job_id, title, company, compensation_value, compensation_period
-- FROM jobs 
-- WHERE compensation_value >= 30
-- AND compensation_period = 'per hour'
-- AND is_active = TRUE;

-- 5. Full-text search across job titles, companies, and descriptions:
-- SELECT job_id, title, company, 
--        ts_rank(search_vector, query) AS rank
-- FROM jobs, 
--      to_tsquery('english', 'software & engineer') AS query
-- WHERE search_vector @@ query
-- AND is_active = TRUE
-- ORDER BY rank DESC;

-- 6. Get all unique document types required:
-- SELECT DISTINCT jsonb_array_elements_text(application_documents_required) AS document
-- FROM jobs
-- WHERE application_documents_required IS NOT NULL
-- ORDER BY document;

-- 7. Get all unique degrees/disciplines targeted:
-- SELECT DISTINCT jsonb_array_elements_text(targeted_degrees_disciplines) AS degree
-- FROM jobs
-- WHERE targeted_degrees_disciplines IS NOT NULL
-- ORDER BY degree;

-- 8. Find jobs expiring soon (within 7 days):
-- SELECT job_id, title, company, deadline
-- FROM jobs
-- WHERE is_active = TRUE
-- AND deadline >= NOW()
-- AND deadline <= NOW() + INTERVAL '7 days'
-- ORDER BY deadline ASC;

-- 9. Get jobs by competition level (low competition):
-- SELECT job_id, title, company, openings, applications, chances
-- FROM jobs
-- WHERE is_active = TRUE
-- AND chances > 0.3  -- More than 30% acceptance rate
-- ORDER BY chances DESC;

-- 10. Get recently added jobs (last 24 hours):
-- SELECT job_id, title, company, scraped_at
-- FROM jobs
-- WHERE scraped_at >= NOW() - INTERVAL '24 hours'
-- ORDER BY scraped_at DESC;

-- ============================================================================
-- NOTES FOR DEVELOPERS
-- ============================================================================

-- JSONB Array Operations:
-- - Use @> to check if array contains element: 
--   WHERE array_column @> '["value"]'::jsonb
-- - Use jsonb_array_elements_text() to extract array elements
-- - GIN indexes make these operations fast

-- Full-Text Search:
-- - search_vector automatically updates when job content changes
-- - Use ts_rank() to sort by relevance
-- - Combine terms with & (AND), | (OR), ! (NOT)

-- Performance Tips:
-- - Always filter by is_active = TRUE for current jobs
-- - Use ILIKE for case-insensitive text matching
-- - Indexes cover most common query patterns
-- - Consider adding composite indexes for frequent multi-column queries

-- Cost Optimization:
-- - Jobs are shared across all users (single source of truth)
-- - Users only store job_id references in their local databases
-- - Reduces cloud storage costs significantly
-- - Read-heavy workload with efficient indexes

-- ============================================================================
