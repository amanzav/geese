# Documentation

Welcome to the Waterloo Works Automator documentation.

---

## 📚 Available Guides

### **[PRD.md](PRD.md)** ⭐ Start Here
Complete Product Requirements Document:
- What the project does and why it exists
- All features explained (matching, cover letters, workflows)
- Technical architecture and data flow
- Configuration guide and usage modes
- Performance benchmarks and security considerations

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

New users should follow this path:

1. **First Time?** → Start with [README.md](../README.md) for installation
2. **What is this project?** → Read `PRD.md` for complete overview
3. **How does matching work?** → Read `MATCHING_ALGORITHM.md`
4. **How do I use it?** → Read `WORKFLOWS.md`
5. **Cover letter setup?** → Read `LLM_INTEGRATION.md`

---

## 💡 Tips

- All guides assume you've completed the setup in the main README
- Configuration files: `config.json` and `.env`
- Most workflows support custom folder names with `--waterlooworks-folder` flag
- Use `--help` flag on any command to see all options

---

**Questions?** Check the relevant guide above or open an issue on GitHub.
