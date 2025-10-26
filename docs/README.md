# Documentation

Welcome to the Waterloo Works Automator documentation.

---

## 📚 Available Guides

### **[MATCHING_ALGORITHM.md](MATCHING_ALGORITHM.md)**
Complete technical breakdown of the hybrid job matching system:
- Keyword extraction + semantic search + seniority alignment
- Scoring methodology (coverage, skill match, seniority)
- Performance improvements (45x speedup with caching)
- Before/after comparisons with real results

### **[WORKFLOWS.md](WORKFLOWS.md)**
Step-by-step workflows for common tasks:
- Scraping jobs from WaterlooWorks folders
- Generating cover letters in bulk
- Applying to jobs automatically
- Handling external applications and special requirements

### **[LLM_INTEGRATION.md](LLM_INTEGRATION.md)**
Guide to LLM features (Gemini/OpenAI):
- Cover letter generation (personalized, evidence-based)
- Compensation extraction from job descriptions
- Job requirement analysis and categorization
- Configuration and best practices

---

## 🚀 Quick Start

New users should start with the main [README.md](../README.md) in the project root, then explore these guides based on your needs:

1. Want to understand **how matching works**? → Read `MATCHING_ALGORITHM.md`
2. Need to **scrape and apply** to jobs? → Read `WORKFLOWS.md`
3. Want to **generate cover letters**? → Read `LLM_INTEGRATION.md`

---

## 💡 Tips

- All guides assume you've completed the setup in the main README
- Configuration files: `config.json` and `.env`
- Most workflows support custom folder names with `--waterlooworks-folder` flag
- Use `--help` flag on any command to see all options

---

**Questions?** Check the relevant guide above or open an issue on GitHub.
