# Product Requirements Document (PRD)

## Waterloo Works Automator (Geese)

**Version:** 2.0  
**Last Updated:** October 25, 2025  
**Owner:** Aman Zaveri  
**Status:** Production-Ready

---

## 1. Executive Summary

**Waterloo Works Automator (Geese)** is an AI-powered automation system that streamlines the University of Waterloo co-op job application process. The system scrapes job postings from WaterlooWorks, uses semantic AI to match jobs against a student's resume, and automates cover letter generation and job applications.

### Key Value Propositions
- **Time Savings**: Reduces job search from hours to minutes through automation
- **Smart Matching**: AI-powered semantic search finds relevant jobs (not just keyword matching)
- **Quality Applications**: Generates personalized cover letters using LLMs
- **Zero Cost**: Uses free-tier APIs (Gemini) and local models
- **User Control**: Manual review and approval at every critical step

---

## 2. Target Users

### Primary Persona: The Busy UWaterloo Co-op Student
- **Profile**: Engineering/CS student applying to 30-50 co-op positions
- **Pain Points**:
  - Manually browsing hundreds of job postings
  - Writing unique cover letters for each application
  - Missing application deadlines
  - Can't identify which jobs match their skills
- **Goals**: Apply to relevant jobs quickly while maintaining quality

### Secondary Persona: The Strategic Applicant
- **Profile**: Student with specific career goals (e.g., ML/AI roles)
- **Pain Points**:
  - Hard to filter jobs by specific tech stacks
  - Can't rank jobs by fit quality
  - Wants to focus on high-potential opportunities
- **Goals**: Maximize interview chances by applying to best-fit roles

---

## 3. Core Features (Implemented)

### 3.1 Authentication & Session Management
**Status:** ✅ Production

- Automated login to WaterlooWorks portal
- Support for Duo 2FA (manual user approval)
- Session persistence and credential management
- Graceful browser cleanup on errors

**Implementation:**
- Module: `modules/auth.py`
- Credentials stored in `.env` (never committed)
- Uses Selenium WebDriver for browser automation

---

### 3.2 Job Scraping & Data Extraction
**Status:** ✅ Production

**Capabilities:**
- Scrapes all job postings from WaterlooWorks
- Extracts structured data:
  - Job title, company, location
  - Job description and requirements
  - Application deadline
  - Compensation (salary/hourly rate)
  - Special requirements (transcripts, portfolios, external applications)
- Handles pagination automatically
- Incremental saving (every 5 jobs to prevent data loss)

**Modes:**
- **Batch Mode**: Scrape all jobs, then analyze
- **Real-Time Mode**: Scrape → analyze → save per job (see scores live)
- **Quick Mode**: Basic scraping (no detailed analysis)

**Implementation:**
- Module: `modules/scraper.py`
- LLM-powered compensation extraction (`modules/llm_assistant.py`)
- Saves to: `data/jobs_scraped.json`

---

### 3.3 AI-Powered Job Matching
**Status:** ✅ Production (Hybrid Algorithm v2.0)

**How It Works:**

The system uses a **hybrid matching algorithm** combining:
1. **Keyword Matching (35% weight)**: Extracts 80+ technology keywords
2. **Semantic Coverage (40% weight)**: Vector search using sentence transformers
3. **Semantic Strength (10% weight)**: Average similarity of matches
4. **Seniority Alignment (15% weight)**: Job level vs. student experience

**Scoring:**
- Output: 0-100 fit score per job
- Thresholds:
  - 70+: Excellent match (apply immediately)
  - 50-69: Good match (strong candidate)
  - 30-49: Moderate match (consider applying)
  - <30: Weak match (skip)

**Technical Details:**
- Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)
- Vector Search: FAISS (Facebook AI Similarity Search)
- Similarity Threshold: 0.30 (optimized for technical job descriptions)
- Top-K Retrieval: 5 resume bullets per requirement

**Performance:**
- 45x speedup with caching (90s → 2s for 50 jobs)
- Results cached by job ID in `data/job_matches_cache.json`
- Auto-invalidates cache when algorithm changes

**Implementation:**
- Module: `modules/matcher.py`
- Embeddings: `modules/embeddings.py`
- Configuration: `config.json` → `matcher` section

**See:** [MATCHING_ALGORITHM.md](MATCHING_ALGORITHM.md) for technical deep-dive

---

### 3.4 Smart Filtering & Ranking
**Status:** ✅ Production

**Filtering Criteria:**
- Preferred locations (e.g., Toronto, Remote, Waterloo)
- Keyword matching (e.g., Python, AI, Full Stack)
- Company blacklist (avoid specific employers)
- Minimum fit score threshold (default: 30)

**Output:**
- Jobs sorted by fit score (highest first)
- Displays: title, company, location, score breakdown
- Shows matched technologies and missing skills
- Color-coded by score range (🟢🟡🟠🔴)

**Implementation:**
- Module: `modules/filter_engine.py`, `modules/filtering.py`
- Configuration: `config.json` → `preferred_locations`, `keywords_to_match`, `companies_to_avoid`

---

### 3.5 Auto-Save to WaterlooWorks Folders
**Status:** ✅ Production

**Feature:**
Automatically saves high-scoring jobs to a WaterlooWorks folder for later application.

**How It Works:**
1. System analyzes jobs and calculates fit scores
2. Jobs meeting threshold (default: 30) are identified
3. Browser navigates to each job posting
4. Job is saved to configured WaterlooWorks folder (default: "geese")

**Usage:**
```bash
python main.py --realtime --auto-save
```

**Configuration:**
```json
{
  "matcher": {
    "auto_save_threshold": 30
  },
  "waterlooworks_folder": "geese"
}
```

**Implementation:**
- Module: `modules/pipeline.py`
- Uses existing Selenium session (no re-login needed)

---

### 3.6 Cover Letter Generation
**Status:** ✅ Production

**Feature:**
Generates personalized, evidence-based cover letters using LLMs (Gemini 2.0 Flash or OpenAI GPT-4).

**Capabilities:**
- Analyzes job description + resume
- Generates 100-400 word cover letters
- Highlights relevant experience for specific role
- Saves as Word (.docx) and PDF
- Batch generation for all jobs in a folder

**Evidence-Based Approach:**
- Only uses matched resume bullets (no hallucinations)
- Focuses on job-specific requirements
- Maintains professional, enthusiastic tone

**Usage:**
```bash
# Generate covers for all jobs in Geese folder
python main.py --mode cover-letter

# Or use folder scraper for specific folders
python main.py --mode scrape-folder --waterlooworks-folder "FOLDER_NAME"
python main.py --mode generate-folder-covers --waterlooworks-folder "FOLDER_NAME"
```

**Implementation:**
- Module: `modules/cover_letter_generator.py`
- LLM Client: `modules/llm_assistant.py`
- Template: `templates/template.docx`
- Output: `cover_letters/{Company}_{Title}.pdf`

**Configuration:**
```json
{
  "cover_letter": {
    "template_path": "template.docx",
    "prompt_template": "..."
  },
  "matcher": {
    "llm_provider": "gemini"  // or "openai"
  }
}
```

**Cost:**
- Gemini 2.0 Flash: **FREE** (15 RPM, 1M TPM)
- OpenAI GPT-3.5: ~$0.002 per cover letter
- OpenAI GPT-4: ~$0.03 per cover letter

**See:** [LLM_INTEGRATION.md](LLM_INTEGRATION.md) for details

---

### 3.7 Folder-Based Workflows
**Status:** ✅ Production

**Feature:**
Scrape, analyze, and apply to jobs from any WaterlooWorks folder.

**Workflow:**
1. **Scrape Folder**: Extract all jobs from a specific WW folder
2. **Generate Covers**: Create cover letters for all jobs
3. **Apply Automatically**: Upload covers and submit applications

**Special Handling:**
- External applications (provides URLs for manual application)
- Extra document requirements (transcripts, portfolios)
- Pre-screening questions (optional skip)
- Bonus items (GitHub, portfolio links)

**Usage:**
```bash
# 1. Scrape jobs from "good shit" folder
python main.py --mode scrape-folder --waterlooworks-folder "good shit"

# 2. Generate cover letters
python main.py --mode generate-folder-covers --waterlooworks-folder "good shit"

# 3. Apply to jobs (max 50 applications)
python main.py --mode apply --waterlooworks-folder "good shit" --max-apps 50
```

**Implementation:**
- Module: `modules/folder_scraper.py`
- Application: `modules/apply.py`
- Results saved to: `data/application_report_{timestamp}.md`

**See:** [WORKFLOWS.md](WORKFLOWS.md) for complete guide

---

### 3.8 Cover Letter Upload Automation
**Status:** ✅ Production

**Feature:**
Automatically uploads all generated cover letters to WaterlooWorks job postings.

**How It Works:**
1. Reads all PDFs from `cover_letters/` folder
2. Matches filenames to job postings (format: `{Company}_{Title}.pdf`)
3. Navigates to each job and uploads cover letter
4. Tracks upload status in `data/uploaded_cover_letters.json`
5. Skips already-uploaded covers and recently modified files

**Usage:**
```bash
python main.py --mode upload-covers
```

**Implementation:**
- Module: `modules/cover_letter_generator.py` (upload functionality)
- Tracking: `modules/sync_uploaded_covers.py`

---

## 4. Technical Architecture

### 4.1 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.13+ |
| **Browser Automation** | Selenium WebDriver | 4.15.0+ |
| **AI Embeddings** | Sentence Transformers | 3.0.1 |
| **Vector Search** | FAISS | 1.8.0+ |
| **LLM** | Google Gemini 2.0 Flash | Free Tier |
| **PDF Parsing** | PyPDF | 5.0.1 |
| **Document Generation** | python-docx | - |
| **PDF Conversion** | pywin32 (Windows) | - |

### 4.2 Project Structure

```
waterloo_works_automator/
├── main.py                      # CLI entry point
├── config.json                  # User configuration
├── .env                         # Credentials (gitignored)
├── requirements.txt             # Dependencies
│
├── modules/
│   ├── auth.py                  # WaterlooWorks authentication
│   ├── scraper.py               # Job scraping logic
│   ├── matcher.py               # AI matching + scoring
│   ├── embeddings.py            # Sentence transformers + FAISS
│   ├── filter_engine.py         # Job filtering logic
│   ├── cover_letter_generator.py # LLM cover letter generation
│   ├── llm_assistant.py         # LLM client (Gemini/OpenAI)
│   ├── folder_scraper.py        # Folder-specific workflows
│   ├── apply.py                 # Auto-apply automation
│   ├── pipeline.py              # Main orchestration
│   ├── cli.py                   # Command-line interface
│   └── utils.py                 # Helper functions
│
├── data/
│   ├── resume_parsed.txt        # Extracted resume bullets
│   ├── jobs_scraped.json        # Raw scraped jobs
│   ├── job_matches_cache.json   # Cached match scores
│   ├── matches_{timestamp}.json # Match results
│   └── uploaded_cover_letters.json # Upload tracking
│
├── cover_letters/               # Generated cover letters (PDFs)
├── templates/                   # Cover letter templates
├── input/                       # User resume (PDF)
├── embeddings/resume/           # Cached resume embeddings
│
├── docs/
│   ├── README.md                # Documentation index
│   ├── MATCHING_ALGORITHM.md    # Technical deep-dive
│   ├── WORKFLOWS.md             # Usage guides
│   ├── LLM_INTEGRATION.md       # LLM features
│   └── PRD.md                   # This document
│
└── tests/                       # Unit tests
```

### 4.3 Data Flow

```
1. User Authentication
   └─> WaterlooWorks login (Duo 2FA)

2. Job Discovery
   └─> Scrape jobs → Extract data → Save JSON

3. Resume Processing
   └─> Parse PDF → Extract bullets → Generate embeddings → Build FAISS index

4. Job Matching
   └─> For each job:
       ├─> Extract requirements
       ├─> Keyword matching (tech stack)
       ├─> Semantic search (vector similarity)
       ├─> Calculate hybrid score
       └─> Cache results

5. Filtering & Ranking
   └─> Apply filters → Sort by score → Display results

6. Cover Letter Generation
   └─> For high-scoring jobs:
       ├─> Send job + matched bullets to LLM
       ├─> Generate personalized letter
       ├─> Convert to PDF
       └─> Save to cover_letters/

7. Application
   └─> For each job:
       ├─> Navigate to posting
       ├─> Upload cover letter
       ├─> Fill out form
       └─> Submit application
```

---

## 5. Configuration

### 5.1 Environment Variables (`.env`)

```env
# WaterlooWorks Credentials
WATERLOOWORKS_USERNAME=your_username
WATERLOOWORKS_PASSWORD=your_password

# LLM API Keys (choose one)
GOOGLE_API_KEY=your_gemini_key     # Recommended (free)
OPENAI_API_KEY=your_openai_key     # Alternative (paid)
```

### 5.2 Application Config (`config.json`)

**Key Settings:**

```json
{
  "resume_path": "input/resume.pdf",
  
  "matcher": {
    "similarity_threshold": 0.30,      // Semantic match threshold
    "min_match_score": 30,             // Minimum score to show
    "auto_save_threshold": 30,         // Auto-save jobs with score ≥ 30
    "llm_provider": "gemini",          // or "openai"
    "weights": {
      "keyword_match": 0.35,           // Explicit tech matching
      "semantic_coverage": 0.40,       // % requirements met
      "semantic_strength": 0.10,       // How well you meet them
      "seniority_alignment": 0.15      // Level match
    }
  },
  
  "waterlooworks_folder": "geese",     // Target folder name
  "preferred_locations": ["Toronto", "Remote", "Waterloo"],
  "keywords_to_match": ["Python", "AI", "ML"],
  "companies_to_avoid": []
}
```

---

## 6. Usage Modes

### 6.1 Real-Time Mode (Recommended)
```bash
python main.py --realtime --auto-save
```
- Scrape → analyze → show score → save (per job)
- See results instantly
- Best for discovering new postings

### 6.2 Batch Mode
```bash
python main.py --mode batch
```
- Scrape all jobs first, then analyze
- Best for processing large job lists

### 6.3 Analyze Only (Cached)
```bash
python main.py --mode analyze --jobs-path data/jobs_scraped.json
```
- Analyze previously scraped jobs
- No scraping (uses cache)
- 45x faster with cached matches

### 6.4 Cover Letter Generation
```bash
python main.py --mode cover-letter
```
- Generate covers for all jobs in Geese folder
- Uses LLM (Gemini/OpenAI)

### 6.5 Upload Covers
```bash
python main.py --mode upload-covers
```
- Upload all PDFs from `cover_letters/` to WaterlooWorks

### 6.6 Folder Workflows
```bash
# Complete workflow for "good shit" folder
python main.py --mode scrape-folder --waterlooworks-folder "good shit"
python main.py --mode generate-folder-covers --waterlooworks-folder "good shit"
python main.py --mode apply --waterlooworks-folder "good shit" --max-apps 50
```

---

## 7. Performance & Scalability

### 7.1 Speed Benchmarks
- **Initial scrape**: ~5-10 seconds per job (50 jobs ≈ 5-8 minutes)
- **Cached analysis**: 2 seconds for 50 jobs (45x speedup)
- **Real-time mode**: ~8-12 seconds per job (scrape + analyze + save)
- **Cover letter generation**: ~3-5 seconds per letter

### 7.2 Caching Strategy
- **Match results**: Cached by job ID (invalidates on algorithm changes)
- **Resume embeddings**: Built once, reused for all jobs
- **FAISS index**: Saved to disk, loaded on startup
- **Scraped jobs**: Persisted to JSON for offline analysis

### 7.3 Resource Usage
- **Memory**: ~200-300 MB (FAISS index + embeddings)
- **Disk**: ~10-20 MB per 100 jobs (JSON + cache)
- **CPU**: Embedding generation (one-time) is compute-intensive
- **Network**: WaterlooWorks scraping (Selenium overhead)

---

## 8. Security & Privacy

### 8.1 Data Handling
- Resume data stays **100% local** (never sent to cloud)
- Only matched bullets sent to LLM (not full resume)
- Credentials stored in `.env` (gitignored)
- No telemetry or analytics

### 8.2 Best Practices
- Review all cover letters before submission
- Don't share API keys
- Use environment variables for credentials
- Regularly clear cached data if needed

---

## 9. Limitations & Constraints

### 9.1 Current Limitations
- **Manual 2FA**: Duo authentication requires user approval
- **Single-threaded**: Processes jobs sequentially (no parallelization)
- **WaterlooWorks dependency**: Breaks if UI changes significantly
- **Windows-only PDF conversion**: Uses `pywin32` (no Mac/Linux support yet)

### 9.2 Known Issues
- Pre-screening questions not auto-answered (manual intervention required)
- External applications must be submitted manually
- Cover letter quality varies with LLM provider/model

---

## 10. Future Roadmap

### Phase 1: Enhancements (Near-term)
- [ ] Multi-threaded scraping (parallel job processing)
- [ ] Cross-platform PDF conversion (Mac/Linux support)
- [ ] Resume optimization suggestions
- [ ] Interview preparation insights from matched jobs

### Phase 2: Advanced Features (Mid-term)
- [ ] Web dashboard for job visualization
- [ ] Historical tracking (matches → interviews → offers)
- [ ] A/B testing for cover letter approaches
- [ ] Custom skill taxonomies per domain

### Phase 3: Ecosystem (Long-term)
- [ ] Browser extension for live job analysis
- [ ] Mobile app for on-the-go management
- [ ] Integration with LinkedIn/Indeed
- [ ] Community-driven job insights

---

## 11. Success Metrics

### 11.1 Current Metrics (As of Oct 2025)
- **Matching Accuracy**: 55% improvement over naive approach (47 → 73 for top job)
- **Performance**: 45x speedup with caching (90s → 2s for 50 jobs)
- **Coverage**: 0% → 62.5% semantic coverage (fixed algorithm)
- **User Adoption**: 1 active user (creator), preparing for public release

### 11.2 Target Metrics (Post-Launch)
- 100+ active users (UWaterloo students)
- 90%+ user satisfaction (positive feedback)
- <5% error rate (failed applications/scrapes)
- 10x time savings vs. manual process

---

## 12. Support & Maintenance

### 12.1 Documentation
- Main README: Getting started guide
- Technical docs in `docs/` folder
- Inline code comments for developers
- This PRD for product overview

### 12.2 Community
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Q&A and general support
- Pull Requests: Community contributions welcome

### 12.3 Maintenance Plan
- Quarterly dependency updates
- WaterlooWorks UI change monitoring
- LLM model upgrades (Gemini 2.5, GPT-5, etc.)
- Performance profiling and optimization

---

## 13. Conclusion

**Waterloo Works Automator (Geese)** is a production-ready, AI-powered job application system that solves real pain points for UWaterloo co-op students. With intelligent matching, automated cover letter generation, and streamlined workflows, it reduces the job search process from hours to minutes while maintaining quality and personalization.

**Key Differentiators:**
- ✅ **Zero Cost**: Free-tier APIs (Gemini) and local models
- ✅ **Evidence-Based**: No LLM hallucinations (only matched bullets used)
- ✅ **User Control**: Manual review and approval at every step
- ✅ **Production-Ready**: Tested, cached, and optimized

**Ready for public release.**

---

**Last Updated:** October 25, 2025  
**Version:** 2.0  
**Status:** 🟢 Production
