# Documentation

## Current Documentation

### **ALGORITHM_IMPROVEMENTS.md**
Complete technical breakdown of the hybrid matching algorithm improvements (October 2024). Covers:
- Problems identified (terrible parsing, weak scoring, hidden tech)
- Solutions implemented (keyword extraction, fluff filtering, hybrid scoring)
- Performance gains (55% higher scores, 45x speedup with caching)

### **CACHING_GUIDE.md**
Comprehensive guide to the match caching system. Includes:
- How caching works (job ID-based storage)
- Usage examples (`--force-rematch`, cache clearing)
- Performance comparison (90s → 2s for 50 jobs)
- Implementation details and future enhancements

### **LLM.md**
Future LLM integration plans for cover letter generation and application insights.
**Status:** Not implemented yet

---

## Archive

Planning and review documents from project inception (moved to `archive/`):
- `PRD.md` - Original product requirements
- `MVP.md` - MVP feature planning
- `MATCHER_REVIEW.md` - Initial architecture review

These are kept for historical reference but don't reflect current implementation.
