# Match Caching System - Visual Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     WATERLOO WORKS AUTOMATOR                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ 1. SCRAPING  │
└──────┬───────┘
       │ Scrapes jobs from WaterlooWorks
       │ Saves to: data/jobs_scraped.json
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                   data/jobs_scraped.json                          │
│                                                                   │
│  [                                                                │
│    {"id": "440414", "title": "AI Agent Dev", ...},              │
│    {"id": "440426", "title": "AI Software Eng", ...},           │
│    ...                                                            │
│  ]                                                                │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐       ┌──────────────────────────────────────────┐
│ 2. MATCHING  │◄──────│  CACHE CHECK                              │
└──────┬───────┘       │  - Is job ID in cache?                   │
       │               │  - Is force_rematch enabled?             │
       │               │                                            │
       │               │  YES → Use cached match (0.01s) ✨       │
       │               │  NO  → Calculate match (1-2s)            │
       │               └──────────────────────────────────────────┘
       │
       │ For each job:
       │   1. Check cache (job_matches_cache.json)
       │   2. If cached: return stored result
       │   3. If not: calculate using AI embeddings
       │   4. Save to cache
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│              data/job_matches_cache.json (NEW!)                   │
│                                                                   │
│  {                                                                │
│    "440414": {                                                    │
│      "fit_score": 73.0,                                          │
│      "coverage": 100.0,                                          │
│      "skill_match": 4.2,                                         │
│      "seniority_alignment": 80.0,                                │
│      "last_updated": "2025-10-12T12:50:51"                       │
│    },                                                             │
│    "440426": { ... }                                             │
│  }                                                                │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ 3. FILTERING │  Apply location, keyword, company filters
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. RESULTS   │  Save to matches_TIMESTAMP.json + .md
└──────────────┘
```

## Cache Hit vs Miss Flow

### CACHE HIT (Existing Job) ✅
```
Job ID "440414" →  Check Cache  →  FOUND! ✓
                       ↓
                   Return cached result (0.01s)
                       ↓
                   Move to next job
```

### CACHE MISS (New Job) 🔍
```
Job ID "440999" →  Check Cache  →  NOT FOUND ✗
                       ↓
                   Calculate match:
                   - Parse requirements
                   - Generate embeddings
                   - Search resume vectors
                   - Calculate scores (1-2s)
                       ↓
                   Save to cache
                       ↓
                   Return result
```

## Performance Timeline

### First Run (No Cache)
```
Time: ████████████████████████████████████████████████ 90s
Jobs: [J1][J2][J3]...[J50] - All analyzed from scratch
```

### Second Run (All Cached)
```
Time: ██ 2s  (45x faster!)
Jobs: [✓][✓][✓]...[✓] - All from cache
```

### Incremental Run (10 New, 40 Cached)
```
Time: ██████████ 20s  (4.5x faster!)
Jobs: [✓][✓]...[✓][J41][J42]...[J50]
      ↑ Cached  ↑ New jobs analyzed
```

## Command Flow

```
┌─────────────────────────────────────┐
│  python main.py --cached            │  
└─────────────────┬───────────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Load jobs_scraped.json    │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Load match cache          │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  For each job:             │
    │   - Check cache            │
    │   - Use or calculate       │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Save results              │
    └────────────────────────────┘


┌────────────────────────────────────────┐
│  python main.py --cached --force-rematch│  
└─────────────────┬──────────────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Load jobs_scraped.json    │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  IGNORE cache              │ ⚠️  
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Recalculate ALL jobs      │
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Update cache              │
    └────────────────────────────┘
```

## Cache Benefits Summary

| Benefit | Description | Impact |
|---------|-------------|--------|
| 🚀 **Speed** | 45x faster for cached jobs | 90s → 2s |
| 🎯 **Incremental** | Only analyzes new jobs | Smart & efficient |
| 💾 **Persistent** | Survives crashes/restarts | Reliable |
| 🔄 **Flexible** | Force refresh anytime | User control |
| 📊 **Transparent** | Shows cache hits/misses | Clear feedback |

## Files Involved

```
data/
├── jobs_scraped.json          # Raw job data
├── job_matches_cache.json     # Match scores (NEW!)
├── resume_parsed.txt          # Your resume
└── matches_TIMESTAMP.json     # Final results

embeddings/resume/
├── index.faiss                # Resume vectors
└── metadata.json              # Resume bullets mapping
```
