# 🎯 Waterloo Works Automator

**Automatically scrape, analyze, and match WaterlooWorks jobs to your resume using AI.**

Built by Aman Zaveri for UWaterloo co-op job search automation.

---

## 🌟 Features

✅ **Automated Scraping**: Log in and scrape all WaterlooWorks job postings  
✅ **AI-Powered Matching**: Semantic search using sentence transformers (understands meaning, not just keywords)  
✅ **Smart Caching**: Match results cached by job ID - only analyzes new jobs (45x faster!)  
✅ **Incremental Saving**: Jobs saved every 5 scrapes - never lose progress to crashes  
✅ **Smart Scoring**: Weighted scoring based on coverage, skill match, and seniority alignment  
✅ **Filtering**: Filter by location, keywords, and companies  
✅ **Reports**: Generate JSON and Markdown reports of best matches  

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Preferences

Edit `config.json`:
```json
{
  "preferred_locations": ["Toronto", "Waterloo", "Remote"],
  "keywords_to_match": [],  // Leave empty to match all jobs
  "companies_to_avoid": [],
  "matcher": {
    "min_match_score": 30  // Only show jobs with 30+ fit score
  }
}
```

### 3. Update Your Resume

Place your resume bullets in `data/resume_parsed.txt` (one bullet per line).

Or place a PDF resume in `input/resume.pdf` - it will auto-extract bullets.

### 4. Run!

**Option A: Full Pipeline (Scrape + Analyze)**
```bash
python main.py
```

**Option B: Quick Mode (Faster, less detail)**
```bash
python main.py --quick
```

**Option C: Use Cached Jobs (Test without scraping)**
```bash
python main.py --cached
```

**Option D: Force Rematch (Recalculate all scores)**
```bash
python main.py --cached --force-rematch
```

**Option E: Test with Sample Jobs**
```bash
python test_analyze.py
```

> **💡 Tip:** After first run, use `--cached` to analyze jobs instantly (uses cached matches). See [Caching Guide](docs/CACHING.md) for details.

---

## 📊 How It Works

### The Pipeline

```
1. Scrape Jobs           →  2. Extract Requirements  →  3. Vector Search
   (WaterlooWorks)           (Parse job description)     (Find matching bullets)
                                                                ↓
5. Show Results          ←  4. Calculate Fit Score   ←  (Coverage + Skills + Seniority)
   (Sorted by score)         (0-100 weighted score)
```

### The Scoring System

**Fit Score = Weighted Sum of 3 Components:**

1. **Coverage (60%)**: What % of job requirements are matched by your resume?
2. **Skill Match (25%)**: How strong are the matches?
3. **Seniority Alignment (15%)**: Does your experience level fit?

**Example:**
```
Job: Full Stack Engineer at Amazon
Coverage: 62.5% (5/8 requirements matched)
Skill Match: 16.4% (similarity ~0.50)
Seniority: 80% (co-op role, some leadership)

Fit Score = (0.60 × 62.5) + (0.25 × 16.4) + (0.15 × 80) = 53.6/100 🟡
```

### Semantic Search (The AI Part)

- Converts resume bullets to 384-dimensional vectors
- Uses FAISS for fast similarity search
- Understands meaning, not just keywords
- Model: `sentence-transformers/all-MiniLM-L6-v2`

---

## 📁 Project Structure

```
waterloo_works_automator/
├── main.py                  # Main pipeline (scrape → analyze → save)
├── test_analyze.py          # Test with sample jobs
├── config.json              # Your preferences
│
├── modules/
│   ├── auth.py              # WaterlooWorks login (SSO + Duo 2FA)
│   ├── scraper.py           # Job scraping
│   ├── embeddings.py        # AI embeddings + FAISS search
│   ├── matcher.py           # Job-resume matching + scoring
│   └── utils.py             # Helper functions
│
├── data/
│   ├── resume_parsed.txt    # Your resume bullets
│   ├── jobs_scraped.json    # Raw scraped jobs
│   └── matches_*.json       # Match results
│
└── tests/                   # Test scripts
```

---

## 🎯 Example Results

```
📊 RESULTS (Sorted by Fit Score)

🟡 #1 - Fit Score: 53.6/100
   📋 Full Stack Engineer - Co-op
   🏢 Amazon - Toronto, ON
   📈 Coverage: 62.5% | Skills: 16.4% | Seniority: 80.0%

🟠 #2 - Fit Score: 43.1/100
   📋 Software Developer - Backend
   🏢 Shopify - Toronto, ON
   📈 Coverage: 50.0% | Skills: 10.2% | Seniority: 70.0%
```

**Interpretation:**
- 🟢 Excellent (70+): Apply ASAP!
- 🟡 Good (50-69): Strong candidate
- 🟠 Moderate (30-49): Worth considering
- 🔴 Weak (<30): Probably skip

---

## 📝 Development Status

- ✅ **Phase 1:** Authentication & Job Scraping
- ✅ **Phase 2:** Resume Matching (AI-powered semantic search)
- 📋 **Phase 3:** LLM Insights (optional)
- 💾 **Phase 4:** Job Management & Tracking
- 🤖 **Phase 5:** Auto-Apply Automation

---

## 🛠️ Technologies

- Python 3.13
- Selenium (browser automation)
- Sentence Transformers 5.1.1 (AI embeddings)
- FAISS 1.12.0 (vector search)
- PyPDF 5.0.1 (resume parsing)

---

## 👤 Author

**Aman Zaveri**  
University of Waterloo - Mechatronics Engineering, AI Specialization  
[GitHub](https://github.com/amanzav) | [LinkedIn](https://linkedin.com/in/amanzav)

---

**🎯 Happy job hunting! 🚀**
