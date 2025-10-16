# Resume Matcher System - Technical Specification

**Project:** Waterloo Works Automator (Geese)  
**Module:** Resume Matcher & LLM Integration  
**Owner:** Aman Zaveri  
**Version:** 1.0  
**Date:** October 2025  

---

## 1. Overview

The **Resume Matcher System** is a high-quality, zero-cost pipeline that compares Job Descriptions (JD) against your resume to generate:
- Fit score (0-100)
- Matched skills and missing requirements  
- Evidence-based analysis
- Tailored resume bullet suggestions

### Key Capabilities
- Compare job postings to resume using semantic similarity
- Generate match scores with detailed reasoning
- Identify strengths and gaps
- Suggest resume improvements based on evidence

### Architecture Goals
- **Zero Cost**: Uses free-tier services and local models
- **Evidence-Based**: No LLM hallucinations - only matched evidence used
- **Local-First**: Embeddings and processing done locally
- **Optional Cloud**: Can use free-tier APIs (Gemini, Voyage) for enhanced features

---

## 2. Technology Stack

| Component | Technology | Cost | Notes |
|-----------|-----------|------|-------|
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Free | 384-dim, fast, Apache-2.0 license |
| **Vector Index** | FAISS | Free | Cosine similarity via inner product |
| **Reranking** (Optional) | Voyage Rerank / cross-encoder | Free tier | Improves top-k ranking |
| **LLM Reasoning** | Gemini 2.x Flash | Free tier | Alternative: local Llama via Ollama |

### Key Approach
Treat each JD requirement and each resume bullet as separate chunks:
1. **Embed** → Generate vector representations
2. **Retrieve** → Find top-k matches via FAISS
3. **Rerank** (optional) → Refine matches
4. **Score** → Calculate coverage metrics
5. **Reason** → LLM generates insights using only matched evidence

---

## 3. Project Structure

```
geese/
├── modules/
│   ├── auth.py                 # [Existing] Login & session
│   ├── scraper.py              # [Existing] Job scraping
│   ├── utils.py                # [Existing] Helper functions
│   ├── matcher.py              # [NEW] Main matching orchestration + scoring
│   ├── embeddings.py           # [NEW] Embedding generation + FAISS search
│   └── llm_client.py           # [NEW] LLM integration (Gemini/Ollama)
│
├── data/
│   ├── jobs.json               # Scraped jobs from WaterlooWorks
│   ├── resume_parsed.txt       # Extracted resume text (cached)
│   └── synonyms.json           # Optional: Skill synonyms map
│
├── embeddings/
│   └── resume/                 # Cached resume embeddings & FAISS index
│       ├── index.faiss         # FAISS vector index
│       ├── embeddings.npy      # Resume embeddings array
│       └── metadata.json       # Resume bullets mapping
│
├── outputs/
│   └── matches/                # Match results per job
│       └── {job_id}.json       # Individual match results
│
├── input/
│   └── resume.pdf              # User's resume (PDF or DOCX)
│
└── config.json                 # Unified configuration
```

---

## 4. Installation & Setup

### 4.1 Prerequisites
- Python 3.10+
- Virtual environment
- (Optional) Ollama for local LLM

### 4.2 Dependencies

Add to `requirements.txt`:

```txt
# Existing dependencies
selenium>=4.15.0
python-dotenv>=1.0.0

# New dependencies for matcher
sentence-transformers==3.0.1
faiss-cpu==1.8.0.post1
numpy==1.26.4
pyyaml==6.0.2
rapidfuzz==3.9.6
pypdf==5.0.1                    # PDF resume parsing
google-generativeai==0.8.2      # Gemini LLM

# Optional for local reranker
torch>=2.1.0
transformers>=4.42.3
```

### 4.3 Installation

```bash
# Install new dependencies
pip install sentence-transformers faiss-cpu pypdf google-generativeai

# Optional: Install Ollama for local LLM
# Download from https://ollama.ai
```

### 4.4 Environment Variables

Add to `.env`:

```env
# Existing
WATERLOOWORKS_USERNAME=your_username
WATERLOOWORKS_PASSWORD=your_password

# New for matcher
OPENAI_API_KEY=your_api_key         # If using OpenAI
GOOGLE_API_KEY=your_gemini_key      # If using Gemini (recommended)
VOYAGE_API_KEY=your_voyage_key      # Optional for reranking
```

---

## 5. Configuration

### 5.1 Configuration (`config.json`)

Add matcher configuration to existing `config.json`:

```json
{
  "resume_path": "input/resume.pdf",
  "auto_apply_enabled": true,
  "max_applications_per_session": 10,
  
  "matcher": {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "similarity_threshold": 0.65,
    "top_k": 8,
    "llm_provider": "gemini",
    "use_synonyms": false,
    "min_match_score": 70,
    "weights": {
      "required_coverage": 0.60,
      "skill_match": 0.25,
      "seniority_alignment": 0.15
    }
  },
  
  "preferred_locations": ["Toronto", "Remote", "Waterloo"],
  "keywords_to_match": ["Python", "AI", "ML", "Full Stack"],
  "companies_to_avoid": []
}
```

---

## 6. Data Preparation

### 6.1 Resume Format

Place your resume as `input/resume.pdf` or `input/resume.docx`.

The system will:
1. **Auto-extract** text from PDF/DOCX using `pypdf`
2. **Cache** extracted text to `data/resume_parsed.txt`
3. **Parse** into bullets (one per line)

**Manual format** (if auto-extraction fails):

Create `data/resume_parsed.txt` manually:

```txt
Built React Native onboarding flow with TypeScript, app linking, and secure token storage.
Integrated Android NDK C++ module into RN via TurboModules to expose low-level APIs.
Owned CI/CD with Fastlane; managed TestFlight and Play Console staged rollouts.
Developed REST API with Node.js, Express, PostgreSQL; achieved <50ms p95 latency.
```

### 6.2 Synonyms Map (`data/synonyms.json`)

```json
{
  "react native": ["rn", "react-native"],
  "typescript": ["ts"],
  "javascript": ["js"],
  "aws lambda": ["lambda", "λ"],
  "kubernetes": ["k8s"],
  "docker": ["containerization"],
  "postgresql": ["postgres", "psql"],
  "mongodb": ["mongo"]
}
```

---

## 7. Module Specifications

### 7.1 Matcher Module (`modules/matcher.py`)

**Purpose:** Orchestrate the full matching pipeline + scoring logic

**Key Functions:**
- `__init__()` → Load config, initialize embeddings module
- `load_resume(pdf_path)` → Extract text, parse bullets, build index
- `analyze_match(job_data)` → Full pipeline for one job
- `batch_analyze(jobs)` → Process multiple jobs efficiently
- `save_results(job_id, results)` → Persist to JSON

**Scoring Functions:**
- `_calculate_coverage(matches, threshold)` → Required coverage score
- `_calculate_skill_match(jd_skills, resume_skills)` → Skill overlap
- `_calculate_seniority_alignment(jd, resume)` → Level matching
- `_compute_final_score(components)` → Weighted final score

**Pipeline Flow:**
```python
def analyze_match(job_data):
    # 1. Parse job description (use existing scraper data)
    jd_bullets = self._extract_jd_bullets(job_data)
    
    # 2. Embed JD bullets
    jd_embeddings = self.embeddings.encode(jd_bullets)
    
    # 3. Retrieve top matches
    matches = self.embeddings.search(jd_embeddings, top_k=8)
    
    # 4. Calculate scores
    scores = self._calculate_all_scores(matches, job_data)
    
    # 5. LLM reasoning (only if score > threshold)
    if scores['fit_score'] >= 50:
        analysis = self.llm.generate_analysis(job_data, matches, scores)
    else:
        analysis = {"note": "Low match - skipped LLM call"}
    
    # 6. Save results
    result = {**scores, **analysis}
    self.save_results(job_data['id'], result)
    
    return result
```

---

### 7.2 Embeddings Module (`modules/embeddings.py`)

**Purpose:** Handle embedding generation + FAISS vector search

**Key Functions:**
- `__init__(model_name)` → Load sentence-transformers model
- `encode(texts, normalize=True)` → Generate embeddings
- `build_resume_index(resume_bullets)` → Create & save FAISS index
- `load_resume_index()` → Load cached index from disk
- `search(query_embeddings, k)` → Find top-k similar resume bullets

**Implementation:**
```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class EmbeddingsManager:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.resume_bullets = []
    
    def encode(self, texts, normalize=True):
        return self.model.encode(texts, normalize_embeddings=normalize)
    
    def build_resume_index(self, resume_bullets):
        self.resume_bullets = resume_bullets
        embeddings = self.encode(resume_bullets)
        
        # Create FAISS index (inner product = cosine for normalized)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Save to disk
        self._save_index()
    
    def search(self, query_embeddings, k=8):
        distances, indices = self.index.search(
            query_embeddings.astype('float32'), k
        )
        
        # Return matches with resume bullets
        matches = []
        for i, (dists, idxs) in enumerate(zip(distances, indices)):
            match = []
            for dist, idx in zip(dists, idxs):
                match.append({
                    "resume_bullet": self.resume_bullets[idx],
                    "similarity": float(dist),
                    "index": int(idx)
                })
            matches.append(match)
        
        return matches
```

---

### 7.3 LLM Client Module (`modules/llm_client.py`)

**Purpose:** Generate insights using LLM with evidence-only approach

**Key Functions:**
- `__init__(provider='gemini')` → Initialize LLM client
- `generate_analysis(job, matches, scores)` → Get LLM insights
- `_call_gemini(prompt)` → Query Gemini API
- `_call_ollama(prompt)` → Query local Ollama (fallback)
- `_parse_response(response)` → Extract and validate JSON

**Implementation:**
```python
import google.generativeai as genai
import os
import json

class LLMClient:
    def __init__(self, provider='gemini'):
        self.provider = provider
        if provider == 'gemini':
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    def generate_analysis(self, job_data, matches, scores):
        prompt = self._build_prompt(job_data, matches, scores)
        
        try:
            if self.provider == 'gemini':
                response = self._call_gemini(prompt)
            else:
                response = self._call_ollama(prompt)
            
            return self._parse_response(response)
        except Exception as e:
            print(f"LLM error: {e}")
            return {"error": str(e)}
    
    def _build_prompt(self, job_data, matches, scores):
        # Build evidence-only prompt (no full resume/JD)
        prompt_data = {
            "job": {
                "company": job_data['company'],
                "title": job_data['title']
            },
            "matched_evidence": [
                {
                    "jd_requirement": m['jd_bullet'],
                    "resume_match": m['best_match']['resume_bullet'],
                    "similarity": m['best_match']['similarity']
                }
                for m in matches if m['covered']
            ],
            "missing_requirements": [
                m['jd_bullet'] for m in matches if not m['covered']
            ],
            "scores": scores
        }
        
        system_prompt = """You are an ATS/hiring screener. Analyze the job match using ONLY the provided evidence.
        
Return JSON with:
- top_strengths: 2-3 specific matched capabilities
- gaps: 2-3 missing requirements
- keywords_to_add: 3-5 keywords to emphasize
- bullet_suggestions: 2-3 improved resume bullets
- recommendation: "STRONG_MATCH" | "GOOD_MATCH" | "WEAK_MATCH"

Use only the evidence provided. No hallucinations."""
        
        return {
            "system": system_prompt,
            "user": json.dumps(prompt_data, indent=2)
        }
```

---

## 8. Usage Examples

### 8.1 Build Resume Index (One-Time)

```python
from modules.matcher import ResumeMatcher

matcher = ResumeMatcher()

# Auto-extract from PDF and build index
matcher.load_resume("input/resume.pdf")
# Creates:
#   - data/resume_parsed.txt (cached text)
#   - embeddings/resume/index.faiss
#   - embeddings/resume/metadata.json
```

### 8.2 Analyze Single Job

```python
# Job data from scraper
job_data = {
    "id": "12345",
    "title": "Software Developer (AI/ML)",
    "company": "Geotab",
    "city": "Toronto",
    "summary": "Build AI features...",
    "responsibilities": "Ship features end-to-end...",
    "skills": "Python, ML, REST APIs..."
}

result = matcher.analyze_match(job_data)

print(f"✅ Fit Score: {result['fit_score']}/100")
print(f"📊 Coverage: {result['components']['required_coverage']:.2%}")
print(f"\n💪 Strengths:")
for strength in result['top_strengths']:
    print(f"  - {strength}")
print(f"\n⚠️ Gaps:")
for gap in result['gaps']:
    print(f"  - {gap}")
```

### 8.3 Batch Analysis of All Scraped Jobs

```python
import json
from modules.matcher import ResumeMatcher

# Load matcher
matcher = ResumeMatcher()
matcher.load_resume("input/resume.pdf")

# Load all scraped jobs
with open("data/jobs.json") as f:
    jobs = json.load(f)

print(f"📊 Analyzing {len(jobs)} jobs...\n")

# Batch analyze
results = matcher.batch_analyze(jobs)

# Filter by score
high_matches = [r for r in results if r['fit_score'] >= 75]
good_matches = [r for r in results if 60 <= r['fit_score'] < 75]
weak_matches = [r for r in results if r['fit_score'] < 60]

print(f"✅ High matches (75+): {len(high_matches)}")
print(f"👍 Good matches (60-74): {len(good_matches)}")
print(f"⚠️  Weak matches (<60): {len(weak_matches)}")

# Display top matches
print("\n🎯 Top 5 Matches:\n")
for i, result in enumerate(sorted(results, key=lambda x: x['fit_score'], reverse=True)[:5], 1):
    print(f"{i}. {result['company']} - {result['job_title']}")
    print(f"   Score: {result['fit_score']}/100")
    print(f"   Strengths: {', '.join(result['top_strengths'][:2])}")
    print()
```

---

## 9. Output Schema

### 9.1 Match Result (`outputs/matches/{job_id}.json`)

```json
{
  "job_id": "12345",
  "job_title": "Software Developer (AI/ML)",
  "company": "Geotab",
  "analyzed_at": "2025-10-12T10:30:00Z",
  
  "fit_score": 74,
  
  "components": {
    "required_coverage": 0.67,
    "skill_match": 0.75,
    "seniority_alignment": 0.50
  },
  
  "top_strengths": [
    "Direct RN feature delivery with ownership",
    "Native module integration via NDK/TurboModules"
  ],
  
  "gaps": [
    "No explicit GraphQL experience",
    "Release governance not detailed"
  ],
  
  "matched_keywords": [
    "react_native", "typescript", "fastlane", "android_ndk"
  ],
  
  "missing_keywords": [
    "graphql", "firebase"
  ],
  
  "bullet_suggestions": [
    "Led end-to-end React Native releases using Fastlane, TestFlight, and Play Console; owned staged rollouts and crash triage.",
    "Integrated native Android module in C++/NDK and exposed APIs to React Native via TurboModules."
  ],
  
  "evidence": [
    {
      "jd_bullet": "Ship RN features end-to-end",
      "best_resume_bullet": "Built RN onboarding flow with TypeScript...",
      "similarity": 0.78,
      "covered": true
    },
    {
      "jd_bullet": "Integrate native modules (iOS/Android)",
      "best_resume_bullet": "Integrated Android NDK C++ module via TurboModules...",
      "similarity": 0.81,
      "covered": true
    },
    {
      "jd_bullet": "GraphQL API development",
      "best_resume_bullet": null,
      "similarity": 0.32,
      "covered": false
    }
  ]
}
```

---

## 10. CLI Integration

Add to `geese.py` main menu:

```python
def main():
    print("🪿 Geese - WaterlooWorks Automation\n")
    print("1. 🔑 Login to WaterlooWorks")
    print("2. 📊 Scrape Job Listings")
    print("3. 🎯 Analyze Job Matches")      # NEW
    print("4. 🔍 Browse High Matches")       # NEW
    print("5. 💾 Save Selected Jobs")
    print("6. 🤖 Auto-Apply to Saved Jobs")
    print("7. 📈 View Application Status")
    print("8. ⚙️  Settings")
    print("9. 🚪 Exit")
```

---

## 11. Testing Plan

### 11.1 Unit Tests

```python
# tests/test_matcher.py
def test_parse_resume():
    resume = parse_resume("data/test_resume.txt")
    assert len(resume.bullets) > 0
    assert "python" in resume.skills

def test_embeddings():
    texts = ["Built React app", "Developed API"]
    embeddings = encode_texts(texts)
    assert embeddings.shape == (2, 384)

def test_scoring():
    score = calculate_coverage(matches, threshold=0.65)
    assert 0.0 <= score <= 1.0
```

### 11.2 Integration Tests

```python
def test_full_pipeline():
    matcher = ResumeMatcher()
    matcher.build_resume_index("input/resume.txt")
    
    job = load_test_job()
    result = matcher.analyze_match(job)
    
    assert "fit_score" in result
    assert 0 <= result["fit_score"] <= 100
    assert "evidence" in result
```

---

## 12. Performance Optimization

### 12.1 Caching Strategy
- **Resume embeddings**: Build once, reuse for all jobs
- **FAISS index**: Save to disk, load on startup
- **Synonyms**: Load once into memory

### 12.2 Batch Processing
- Process multiple jobs in parallel
- Use batch encoding for efficiency
- Cache LLM responses for similar jobs

### 12.3 Thresholds
- **Similarity threshold**: 0.65 (adjust based on results)
- **Top-k retrieval**: 8 candidates per JD bullet
- **Min score for "good match"**: 70+

---

## 13. Error Handling

### 13.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Low similarity scores | Resume/JD terminology mismatch | Expand synonyms.json |
| LLM hallucinations | Sending full resume to LLM | Only send matched evidence |
| Slow performance | No caching | Build resume index once |
| PDF parsing errors | Corrupted PDF | Use .txt format |
| API rate limits | Too many requests | Add delay between calls |

### 13.2 Fallback Strategy
1. Try Gemini API (primary)
2. If fails, try Ollama (local)
3. If both fail, return score only (no LLM insights)

---

## 14. Security & Privacy

### 14.1 Data Handling
- Resume data stays local (never sent to cloud by default)
- Only matched evidence sent to LLM
- API keys stored in `.env` (never committed)
- Results saved locally only

### 14.2 Best Practices
- Review all LLM output before using
- Don't share API keys
- Redact personal info from saved results if sharing
- Use local LLM (Ollama) for sensitive data

---

## 15. Future Enhancements

### Version 0.2.0
- Fine-tuned embedding model for tech jobs
- Custom skill taxonomy per domain
- Multi-resume support (different versions)
- A/B testing for bullet rewrites

### Version 0.3.0
- Real-time matching as jobs are scraped
- Automatic keyword extraction from job trends
- Resume optimization suggestions
- Match confidence intervals

### Version 1.0.0
- Web dashboard for match visualization
- Historical match tracking
- Success rate analysis (matches → interviews)
- Cover letter generation integration

---

## 16. Quick Start Checklist

- [ ] Install dependencies: `pip install sentence-transformers faiss-cpu pypdf google-generativeai`
- [ ] Add `GOOGLE_API_KEY` to `.env`
- [ ] Place resume as `input/resume.txt`
- [ ] Create `data/synonyms.json` with your domain terms
- [ ] Build resume index: `matcher.build_resume_index()`
- [ ] Test with one job: `matcher.analyze_match(job_data)`
- [ ] Review results in `outputs/matches/`
- [ ] Adjust `similarity_threshold` in config if needed
- [ ] Batch process all scraped jobs
- [ ] Filter for high matches (score ≥ 70)

---

## 17. References & Resources

### Documentation
- **Sentence Transformers**: https://www.sbert.net/
- **FAISS**: https://github.com/facebookresearch/faiss
- **Gemini API**: https://ai.google.dev/
- **Ollama**: https://ollama.ai/

### Model Cards
- **all-MiniLM-L6-v2**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Gemini Flash**: https://ai.google.dev/models/gemini

### Papers
- Sentence-BERT: https://arxiv.org/abs/1908.10084
- Dense Passage Retrieval: https://arxiv.org/abs/2004.04906

---

## 18. License & Credits

**License:** MIT  
**Author:** Aman Zaveri  
**Acknowledgments:**
- Sentence Transformers library
- FAISS by Meta Research
- Google Gemini API
- University of Waterloo co-op community

---

**🎯 Let's find your perfect match!**
