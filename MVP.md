# Geese - MVP Specification

**Application Name:** Geese  
**Version:** 0.1.0 (MVP)  
**Owner:** Aman Zaveri  
**Date:** October 2025  

---

## MVP Overview

Geese is an AI-powered automation tool for University of Waterloo co-op students to streamline their WaterlooWorks job application process. The MVP focuses on the core workflow: login → scrape jobs → compare with resume → save matches → auto-apply.

---

## Core MVP Features

### 1. Authentication & Navigation
- ✅ Automated login to WaterlooWorks
- ✅ Handle session management
- ✅ Navigate to job postings page
- ✅ Manual 2FA/Duo authentication support

### 2. Job Discovery & Selection
- ✅ Scrape all available job postings
- ✅ Display job listings in CLI interface
- ✅ Allow user to browse and select jobs
- ✅ Show full job descriptions when selected

### 3. Resume Comparison
- ✅ Load user's base resume
- ✅ Compare job description against resume using LLM
- ✅ Generate match score (0-1)
- ✅ Highlight matching skills/keywords
- ✅ Provide recommendation (apply/skip/maybe)

### 4. Job Management
- ✅ Save selected jobs to a local folder (`saved_jobs/`)
- ✅ Store job details (title, company, description, deadline, URL)
- ✅ Track job status (saved, applied, skipped)
- ✅ Prevent duplicate applications

### 5. Auto-Apply
- ✅ Automatically fill out application forms
- ✅ Upload resume to job application
- ✅ Submit applications automatically
- ✅ Log successful/failed applications
- ✅ Handle basic form variations

---

## MVP User Flow

```
1. User runs: python geese.py
   ↓
2. Login to WaterlooWorks
   - Enter credentials (or use saved session)
   - Complete 2FA manually
   ↓
3. Scrape Job Listings
   - Extract all job postings
   - Store in memory + save to data/jobs.json
   ↓
4. Browse & Select Jobs
   - CLI displays job list
   - User can view full descriptions
   - User selects jobs of interest
   ↓
5. Compare with Resume
   - LLM analyzes job vs resume
   - Shows match score & reasoning
   - User confirms to save
   ↓
6. Save to Folder
   - Job saved to saved_jobs/{company}_{title}/
   - Stores job details as JSON
   - Marks as "saved" in tracker
   ↓
7. Auto-Apply (Optional)
   - User selects saved jobs to apply to
   - Geese automatically fills forms
   - Uploads resume
   - Submits application
   - Updates status to "applied"
```

---

## MVP File Structure

```
geese/
├── geese.py                    # Main entry point
├── config.json                 # User configuration
├── requirements.txt            # Python dependencies
│
├── modules/
│   ├── auth.py                # Login & session management
│   ├── scraper.py             # Job scraping logic
│   ├── matcher.py             # Resume comparison (LLM)
│   ├── saver.py               # Save jobs to folder
│   ├── applicator.py          # Auto-apply logic
│   └── cli.py                 # CLI interface
│
├── data/
│   ├── jobs.json              # All scraped jobs
│   ├── applied.json           # Application tracker
│   └── session.pkl            # Saved browser session
│
├── saved_jobs/                # Folder for saved job listings
│   ├── Geotab_Software_Developer/
│   │   ├── job.json
│   │   └── analysis.json
│   └── ...
│
├── input/
│   └── resume.pdf             # User's base resume
│
└── logs/
    └── geese.log              # Application logs
```

---

## MVP Technical Requirements

### Core Dependencies
```txt
selenium>=4.15.0
playwright>=1.40.0
openai>=1.3.0
python-dotenv>=1.0.0
rich>=13.7.0          # For beautiful CLI
click>=8.1.7          # For CLI commands
```

### Environment Variables (.env)
```env
WATERLOOWORKS_USERNAME=your_username
WATERLOOWORKS_PASSWORD=your_password
OPENAI_API_KEY=your_api_key
```

---

## MVP Data Schemas

### 1. Job Object (`data/jobs.json`)
```json
{
  "id": "12345",
  "title": "Software Developer (AI/ML)",
  "company": "Geotab",
  "location": "Toronto, ON",
  "deadline": "2025-10-17",
  "description": "Full job description...",
  "url": "https://waterlooworks.uwaterloo.ca/job/12345",
  "scraped_at": "2025-10-11T10:30:00Z",
  "status": "new"
}
```

### 2. Saved Job (`saved_jobs/{company}_{title}/job.json`)
```json
{
  "id": "12345",
  "title": "Software Developer (AI/ML)",
  "company": "Geotab",
  "location": "Toronto, ON",
  "deadline": "2025-10-17",
  "description": "Full job description...",
  "url": "https://waterlooworks.uwaterloo.ca/job/12345",
  "saved_at": "2025-10-11T11:00:00Z",
  "status": "saved"
}
```

### 3. Match Analysis (`saved_jobs/{company}_{title}/analysis.json`)
```json
{
  "job_id": "12345",
  "match_score": 0.87,
  "matched_keywords": ["Python", "AI/ML", "Full-Stack", "REST APIs"],
  "missing_skills": ["Kubernetes", "GraphQL"],
  "recommendation": "STRONG MATCH - Apply",
  "reasoning": "Your experience with Python ML frameworks and full-stack development aligns perfectly. Missing K8s is minor.",
  "analyzed_at": "2025-10-11T11:00:00Z"
}
```

### 4. Application Tracker (`data/applied.json`)
```json
{
  "12345": {
    "job_id": "12345",
    "company": "Geotab",
    "title": "Software Developer (AI/ML)",
    "applied_at": "2025-10-11T12:00:00Z",
    "status": "submitted",
    "application_method": "auto",
    "success": true,
    "notes": ""
  }
}
```

### 5. User Config (`config.json`)
```json
{
  "resume_path": "input/resume.pdf",
  "auto_apply_enabled": true,
  "max_applications_per_session": 10,
  "min_match_score": 0.6,
  "preferred_locations": ["Toronto", "Remote", "Waterloo"],
  "keywords_to_match": ["Python", "AI", "ML", "Full Stack"],
  "companies_to_avoid": []
}
```

---

## MVP CLI Commands

### Basic Usage
```bash
# Start Geese (interactive mode)
python geese.py

# Run with specific actions
python geese.py --scrape        # Just scrape jobs
python geese.py --browse        # Browse saved jobs
python geese.py --apply         # Auto-apply to saved jobs
python geese.py --status        # Show application stats
```

### Interactive Flow
```
🪿 Geese - WaterlooWorks Automation

1. 🔑 Login to WaterlooWorks
2. 📊 Scrape Job Listings
3. 🔍 Browse & Select Jobs
4. 💾 Save Selected Jobs
5. 🤖 Auto-Apply to Saved Jobs
6. 📈 View Application Status
7. ⚙️  Settings
8. 🚪 Exit

Select an option [1-8]:
```

---

## MVP Module Specifications

### 1. Authentication Module (`modules/auth.py`)

**Purpose:** Handle WaterlooWorks login and session management

**Functions:**
- `login(username, password)` - Automated login
- `save_session()` - Save browser cookies/session
- `load_session()` - Restore previous session
- `is_logged_in()` - Check if session is valid

**Implementation Notes:**
- Use Selenium/Playwright
- Handle Duo 2FA with manual user intervention
- Save session to avoid repeated logins
- Detect when session expires

---

### 2. Scraper Module (`modules/scraper.py`)

**Purpose:** Extract job postings from WaterlooWorks

**Functions:**
- `scrape_all_jobs()` - Get all available job listings
- `scrape_job_details(job_id)` - Get full job description
- `save_jobs_to_json(jobs)` - Persist scraped data
- `deduplicate_jobs()` - Remove duplicate listings

**Implementation Notes:**
- Parse DOM structure of WaterlooWorks
- Handle pagination if needed
- Extract: title, company, location, deadline, description, URL
- Store raw HTML for backup
- Rate limiting to avoid detection

---

### 3. Matcher Module (`modules/matcher.py`)

**Purpose:** Compare job descriptions with user's resume using LLM

**Functions:**
- `load_resume(path)` - Extract text from PDF/DOCX
- `analyze_match(job, resume)` - LLM-based comparison
- `calculate_score(analysis)` - Generate 0-1 match score
- `extract_keywords(text)` - Find key skills/technologies
- `generate_recommendation(score, analysis)` - Apply/skip/maybe

**LLM Prompt Template:**
```
You are a career advisor helping a co-op student evaluate job matches.

JOB POSTING:
Title: {title}
Company: {company}
Description: {description}

STUDENT RESUME:
{resume_text}

TASK:
1. Calculate a match score (0.0 to 1.0)
2. List matched skills/keywords (from both job and resume)
3. List missing required skills
4. Provide a recommendation: STRONG MATCH | GOOD MATCH | WEAK MATCH | NO MATCH
5. Give 2-3 sentence reasoning

Return as JSON:
{
  "match_score": 0.87,
  "matched_keywords": ["Python", "AI"],
  "missing_skills": ["Kubernetes"],
  "recommendation": "STRONG MATCH",
  "reasoning": "Your Python and AI experience aligns well..."
}
```

---

### 4. Saver Module (`modules/saver.py`)

**Purpose:** Save selected jobs to organized folder structure

**Functions:**
- `save_job(job, analysis)` - Save job + analysis to folder
- `create_job_folder(company, title)` - Generate folder name
- `update_job_status(job_id, status)` - Update tracker
- `get_saved_jobs()` - List all saved jobs
- `delete_saved_job(job_id)` - Remove from saved

**Implementation Notes:**
- Sanitize folder names (remove special chars)
- Handle duplicate company/title combos
- Save both job.json and analysis.json
- Update central tracker (data/applied.json)

---

### 5. Applicator Module (`modules/applicator.py`)

**Purpose:** Automatically fill and submit job applications

**Functions:**
- `auto_apply(job_id)` - Main auto-apply workflow
- `fill_form(form_data)` - Fill application form fields
- `upload_resume(file_path)` - Upload resume file
- `submit_application()` - Click submit button
- `verify_submission()` - Check if application succeeded
- `handle_errors()` - Retry logic for failures

**Implementation Notes:**
- Use Selenium to interact with forms
- Detect form fields dynamically (name, email, resume upload, etc.)
- Handle different form structures
- Screenshot confirmation page
- Log all actions for debugging
- Implement 5-second delay between applications

**Common Form Fields:**
- Name (auto-fill from config)
- Email (auto-fill from config)
- Resume upload
- Cover letter (optional - skip for MVP)
- Available start date
- Checkboxes (agree to terms, etc.)

---

### 6. CLI Module (`modules/cli.py`)

**Purpose:** Beautiful terminal interface for user interaction

**Functions:**
- `show_menu()` - Display main menu
- `display_jobs(jobs)` - Show job listings table
- `show_job_details(job)` - Full job description view
- `prompt_user_selection()` - Get user input
- `show_progress(message)` - Loading spinners
- `display_match_analysis(analysis)` - Show score & reasoning

**Implementation Notes:**
- Use `rich` library for beautiful tables/colors
- Use `click` for CLI commands
- Show loading spinners during scraping/LLM calls
- Color-code match scores (green=high, yellow=medium, red=low)
- Pagination for long job lists

---

## MVP Success Criteria

### Must Have (Blocking)
- ✅ Successfully log into WaterlooWorks
- ✅ Scrape at least 50 job postings
- ✅ Generate match scores for jobs vs resume
- ✅ Save selected jobs to organized folders
- ✅ Auto-apply to at least 1 job successfully

### Should Have (Important)
- ✅ Session persistence (avoid re-login)
- ✅ Handle 80%+ of common form variations
- ✅ Provide useful match analysis (not just scores)
- ✅ Track application history
- ✅ Beautiful CLI experience

### Nice to Have (Optional)
- ⚪ Resume bullet rewriting
- ⚪ Cover letter generation
- ⚪ Email notifications when applied
- ⚪ Export application report

---

## MVP Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 2-3 days | Authentication + scraping working |
| **Phase 2** | 2-3 days | Resume matcher + LLM integration |
| **Phase 3** | 2-3 days | Save jobs + folder structure |
| **Phase 4** | 3-4 days | Auto-apply logic + form handling |
| **Phase 5** | 1-2 days | CLI polish + testing |
| **Total** | ~10-14 days | Full MVP ready |

---

## MVP Testing Plan

### Manual Testing
1. **Login Test**
   - Test with valid credentials
   - Test with invalid credentials
   - Test session persistence
   - Test 2FA flow

2. **Scraping Test**
   - Scrape 10+ jobs
   - Verify all fields extracted correctly
   - Check for duplicates
   - Test with no jobs available

3. **Matching Test**
   - Test with 5 different job types
   - Verify scores make sense
   - Check keyword extraction
   - Ensure reasoning is helpful

4. **Saving Test**
   - Save 5+ jobs
   - Verify folder structure
   - Check JSON format
   - Test duplicate handling

5. **Auto-Apply Test**
   - Apply to 3-5 jobs manually first (to understand forms)
   - Test auto-apply on similar jobs
   - Verify submission success
   - Check error handling

### Edge Cases
- No internet connection
- WaterlooWorks site changes
- PDF resume parsing failures
- LLM API errors
- Form structure variations
- Session expiration mid-process

---

## MVP Known Limitations

1. **2FA/Duo:** Manual intervention required (can't automate)
2. **Form Variations:** May not handle 100% of form types
3. **Cover Letters:** Not generated in MVP (upload blank or skip)
4. **No Web Dashboard:** CLI only for MVP
5. **Single Resume:** Only supports one base resume
6. **No Analytics:** No success tracking or stats
7. **Error Recovery:** Limited retry logic

---

## Post-MVP Enhancements

### Version 0.2.0
- AI-generated cover letters
- Resume bullet rewriting per job
- Better error handling & retries
- Support multiple resume templates
- Email notifications

### Version 0.3.0
- Web dashboard (Next.js)
- Application analytics
- Interview tracking
- Calendar integration for deadlines

### Version 1.0.0
- Multi-user support
- Cloud sync (Supabase)
- Mobile app
- Success rate tracking
- A/B testing for application materials

---

## MVP Security & Ethics

### Security
- Store credentials in `.env` (never commit)
- Use environment variables for API keys
- Save sessions securely (encrypt if possible)
- Clear sensitive data on exit
- Add `.env`, `data/`, `saved_jobs/` to `.gitignore`

### Ethics
- Only scrape your own accessible data
- Respect WaterlooWorks terms of service
- Don't spam applications
- Review all generated content before submission
- User maintains final control over applications
- Implement rate limiting (max 10 apps per session default)

---

## MVP Development Setup

### Prerequisites
```bash
# Install Python 3.10+
python --version

# Install dependencies
pip install -r requirements.txt

# Install browser drivers
playwright install chromium
```

### Environment Setup
```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials
WATERLOOWORKS_USERNAME=your_username
WATERLOOWORKS_PASSWORD=your_password
OPENAI_API_KEY=sk-...
```

### First Run
```bash
# Place your resume in input/
cp /path/to/your/resume.pdf input/resume.pdf

# Run Geese
python geese.py

# Follow interactive prompts
```

---

## MVP Monitoring & Logs

### Log Format (`logs/geese.log`)
```
2025-10-11 10:30:00 [INFO] Geese started
2025-10-11 10:30:05 [INFO] Login successful
2025-10-11 10:30:10 [INFO] Scraping jobs...
2025-10-11 10:30:45 [INFO] Found 127 jobs
2025-10-11 10:31:00 [INFO] Analyzing job #12345
2025-10-11 10:31:05 [INFO] Match score: 0.87
2025-10-11 10:31:10 [INFO] Job saved: Geotab_Software_Developer
2025-10-11 10:32:00 [INFO] Auto-applying to job #12345
2025-10-11 10:32:15 [SUCCESS] Application submitted
2025-10-11 10:32:20 [INFO] Geese session complete
```

### Metrics to Track
- Jobs scraped per session
- Match scores distribution
- Applications submitted
- Success rate (submitted vs failed)
- Time saved vs manual process

---

## Getting Help

### Documentation
- See `README.md` for setup instructions
- See `ARCHITECTURE.md` for technical details
- See `API.md` for module interfaces

### Support
- GitHub Issues: Report bugs or request features
- Email: [your-email]
- Discord: [optional community]

---

## License & Credits

**License:** MIT  
**Author:** Aman Zaveri  
**Acknowledgments:** Built for University of Waterloo co-op students

---

**🪿 Let's help you land that dream co-op!**
