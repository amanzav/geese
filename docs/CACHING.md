# Match Caching System

## Overview

The match caching system prevents redundant calculations by storing job-resume match scores in `data/job_matches_cache.json`. This dramatically speeds up subsequent runs.

## How It Works

### 1. **First Run - Calculate All Matches**
```bash
python main.py --cached
```
- Loads jobs from `data/jobs_scraped.json`
- Calculates match scores for all jobs
- Saves results to `data/job_matches_cache.json`
- Takes ~1-2 seconds per job

### 2. **Subsequent Runs - Use Cache**
```bash
python main.py --cached
```
- Loads jobs from `data/jobs_scraped.json`
- Checks cache for existing matches
- Only calculates matches for NEW jobs
- Reuses cached matches for existing jobs
- Much faster! (~0.01 seconds per cached job)

### 3. **Force Recalculation**
```bash
python main.py --cached --force-rematch
```
- Ignores cache completely
- Recalculates ALL job matches
- Updates cache with new scores
- Useful when you:
  - Update your resume
  - Change matching algorithm
  - Want fresh scores

## Cache File Structure

`data/job_matches_cache.json`:
```json
{
  "440414": {
    "fit_score": 73.0,
    "coverage": 100.0,
    "skill_match": 4.2,
    "seniority_alignment": 80.0,
    "matched_bullets": [
      {"text": "Built AI agents...", "similarity": 0.782},
      ...
    ],
    "requirements_analyzed": 10,
    "last_updated": "2025-10-12T12:50:51.919327"
  },
  ...
}
```

## Performance Comparison

| Operation | Without Cache | With Cache |
|-----------|--------------|------------|
| 50 jobs (first run) | ~90 seconds | ~90 seconds |
| 50 jobs (cached) | ~90 seconds | **~2 seconds** ✨ |
| 50 jobs (10 new) | ~90 seconds | **~20 seconds** ✨ |

## Command Reference

```bash
# Full pipeline (scrape + match)
python main.py                    # Scrapes new jobs, uses cache for matching
python main.py --quick            # Quick scrape mode
python main.py --force-rematch    # Scrapes + recalculates all matches

# Cached mode (no scraping)
python main.py --cached           # Uses cached jobs + matches
python main.py --cached --force-rematch  # Recalculate all from cached jobs
```

## Cache Management

### Clear Match Cache
To force fresh calculations for all jobs:
```bash
# Windows PowerShell
Remove-Item data/job_matches_cache.json

# Then run
python main.py --cached
```

### View Cache Stats
```bash
python -c "import json; cache = json.load(open('data/job_matches_cache.json')); print(f'Cached jobs: {len(cache)}')"
```

## Benefits

✅ **Speed**: 45x faster for cached jobs  
✅ **Incremental**: Only analyzes new jobs  
✅ **Reliable**: Consistent scores across runs  
✅ **Flexible**: Easy to force refresh when needed  
✅ **Efficient**: Saves embeddings computation time  

## Notes

- Cache is tied to job IDs - if a job ID changes, it's treated as new
- Match scores remain stable unless algorithm changes
- Resume embeddings are separately cached in `embeddings/resume/`
- Both caches work together for maximum efficiency
