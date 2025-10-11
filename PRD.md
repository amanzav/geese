# Product Requirements Document (PRD)

## Project: Waterloo Works Automator (WWA)
**Owner:** Aman Zaveri  
**Version:** 1.0  
**Date:** October 2025  

---

## 1. Overview

The **Waterloo Works Automator (WWA)** is a Python-based automation system that streamlines the **University of Waterloo co-op job application process** on WaterlooWorks.

The application:
- Logs into WaterlooWorks (with user credentials or saved session)
- Scrapes job postings (title, company, location, description, deadlines)
- Filters and ranks jobs based on user-defined criteria
- Generates customized resumes and cover letters using an LLM
- Optionally automates job applications

Goal: remove repetitive, manual steps in the WaterlooWorks workflow while maintaining user control and personalization.

---

## 2. Goals & Non-Goals

### Goals
- ✅ Automate repetitive job search and application steps  
- ✅ Enable smart job filtering and ranking  
- ✅ Allow one-click or automated job applications  
- ✅ Use LLMs for personalized resume and cover letter generation  

### Non-Goals (for MVP)
- ❌ Resume parsing or ATS optimization  
- ❌ Interview management  
- ❌ Analytics dashboards or success tracking  

---

## 3. User Personas

### Persona 1 — “The Busy Waterloo Student”
- Needs to apply to dozens of jobs quickly  
- Overwhelmed by job volume  
- Wants keyword filtering and relevance scoring  
- Reviews cover letters before sending  

### Persona 2 — “The Power User”
- Prefers full automation  
- Customizes prompts, filters, and resume templates  
- Tracks applied vs pending jobs  

---

## 4. Functional Requirements

### 4.1 MVP Features

| Feature | Description | Implementation Notes |
|----------|--------------|----------------------|
| **Login Automation** | Secure login to WaterlooWorks | Use Selenium/Playwright; handle Duo 2FA manually |
| **Job Scraping** | Extract all job listings (title, company, location, deadline, description) | Parse DOM; store JSON/CSV |
| **Filtering & Ranking** | Filter by keywords, company, type, location | Keyword scoring + fuzzy match |
| **CLI Dashboard** | Terminal interface to browse and filter | Simple menu-based CLI |
| **Manual Apply Support** | Open job link for user to apply manually | Opens browser URL |

---

### 4.2 Advanced Features (Post-MVP)

| Feature | Description | Implementation Notes |
|----------|--------------|----------------------|
| **AI Resume Tailoring** | Use GPT to rewrite resume bullets for job description | Takes resume + JD context |
| **AI Cover Letter Generator** | Generate personalized cover letters | Template + job context |
| **Auto-Apply Workflow** | Fill forms & upload files automatically | Requires dynamic parsing |
| **Job Tracker** | Record applied and pending jobs | SQLite or Supabase |
| **Web Dashboard** | Next.js + Supabase frontend | Optional later |

---

## 5. System Architecture

### Components

1. **Scraper Module (`scraper.py`)**
   - Handles login, scraping, saving jobs  
   - Uses Selenium/Playwright  

2. **Filter Engine (`filter_engine.py`)**
   - Applies user filters  
   - Calculates keyword match scores  

3. **LLM Assistant (`llm_assistant.py`)**
   - Connects to GPT API or MCP  
   - Generates tailored resumes + cover letters  

4. **Application Manager (`apply_manager.py`)**
   - Handles semi/full automation of applying  
   - Logs application results  

5. **CLI Interface (`run_00_smoke.py`)**
   - Simple text-based workflow  
   - Displays jobs and actions  

6. **Data Layer**
   - Stores jobs and configs in JSON or SQLite  
   - Optional Supabase sync  

---

## 6. User Flow (MVP)

1. **Run script:** `python run_00_smoke.py`  
2. **Login:** Opens browser → user logs in manually  
3. **Scraping:** Collect job postings → save to `/data/jobs.json`  
4. **Filtering:** Ask user for keywords/filters  
5. **Display results:** Sorted job list in CLI  
6. **Apply/Skip:** User selects → opens job URL in browser  

---

## 7. Data Schema

### 7.1 Job Object (`data/jobs.json`)

```json
{
  "id": "12345",
  "title": "Software Developer (AI/ML)",
  "company": "Geotab",
  "location": "Toronto, ON",
  "deadline": "2025-10-17",
  "description": "Responsibilities include...",
  "keywords_matched": ["AI", "Python", "Full-Stack"],
  "match_score": 0.87,
  "status": "pending",
  "url": "https://waterlooworks.uwaterloo.ca/job/12345"
}
```

### 7.2 User Config (`data/user_config.json`)

```json
{
  "filters": {
    "keywords": ["AI", "ML", "Embedded", "Full Stack"],
    "locations": ["Remote", "Toronto"],
    "companies_to_avoid": ["Huawei"],
    "min_score": 0.7
  },
  "resume_path": "data/resumes/base_resume.pdf",
  "cover_letter_template": "templates/cover_letter.txt",
  "max_roles_per_day": 25,
  "open_in_browser": true
}
```

### 7.3 Applied Job Record (SQLite or JSONL)

```json
{
  "job_id": "12345",
  "applied_at": "2025-10-12T03:22:11Z",
  "materials": {
    "resume": "applications/Geotab_Software_Developer/resume.pdf",
    "cover_letter": "applications/Geotab_Software_Developer/cover_letter.md"
  },
  "status": "submitted",
  "notes": "Tailored for ML + telemetry"
}
```

---

## 8. LLM Integration Plan

| Component | Inputs | Outputs | Notes / Prompt Snippet |
|-----------|--------|---------|------------------------|
| Resume Tailoring | Job description, base resume bullets | Rewritten bullets (Markdown) | "Rewrite these bullets to emphasize skills in the JD. Keep quantified results, keep technical nouns, 1–2 lines." |
| Cover Letter | Job description, user profile (projects/skills) | Cover letter (Markdown \| DOCX) | "Write a concise, specific cover letter (≤200 words) referencing 2 strongest matching experiences." |
| Ranking Assistant | Job description, keyword profile | Match score (0–1) + rationale (short) | "Score 0–1. Return {score, 3 reasons, matched_keywords}. Be strict; prefer concrete overlaps." |

---

## 9. Security & Ethics

- Credentials stored locally only; never committed or uploaded.
- Manual login for Duo/2FA in MVP; no password capture.
- All generated materials require user review pre-submission.
- Scrape only your own accessible data; respect site terms.
- Add `.env` and `data/` to `.gitignore` (except safe samples).

---

## 10. Milestones

| Phase | Goal | Deliverables |
|-------|------|--------------|
| 1 | MVP: scrape → filter → CLI review | `run_00_smoke.py`, `scraper.py`, `filter_engine.py`, `data/jobs.json` |
| 2 | LLM: resume + cover letter generation | `llm_assistant.py`, `templates/`, prompts, sample outputs |
| 3 | Auto-apply + tracking | `apply_manager.py`, `db.sqlite`/JSONL tracker, logs |
| 4 | Optional web dashboard | `/frontend` (Next.js), Supabase schema & sync |

---

## 11. Future Enhancements

- Minimal GUI (TUI/desktop) with job cards and preview panel.
- Success analytics (applications → interviews → offers).
- LinkedIn/GitHub enrichment for skill extraction.
- Local fine-tuned model for ranking to cut latency/costs.
- Multi-profile support (different resumes/prompts per role).

---

## 12. Success Metrics

- ⏱ **Time:** 90% reduction in manual application time.
- ⚙️ **Flow:** < 1 minute from filtered list → opened application page.
- 📄 **Data:** 100% structured, deduplicated job extraction.
- 🧠 **LLM:** < 10% manual edits on generated materials (measured over 20+ jobs).

🧠 LLM: < 10% manual edits on generated materials (measured over 20+ jobs).