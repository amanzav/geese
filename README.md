# 🪿 Geese - WaterlooWorks Automation

AI-powered automation tool for University of Waterloo co-op students to streamline their WaterlooWorks job application process.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# WATERLOOWORKS_USERNAME=your_username
# WATERLOOWORKS_PASSWORD=your_password
```

### 3. Run Tests

```bash
# Test authentication
python tests/test_login.py

# Test job scraping
python tests/test_scraper.py
```

## 📁 Project Structure

```
waterloo_works_automator/
├── modules/           # Core modules
│   ├── auth.py       # ✅ Authentication
│   └── scraper.py    # ✅ Job scraping
├── tests/            # Test scripts
│   ├── test_login.py
│   └── test_scraper.py
├── docs/             # Documentation
├── data/             # Scraped data (gitignored)
├── saved_jobs/       # Saved job listings (gitignored)
└── logs/             # Application logs (gitignored)
```

## 📝 Development Status

- ✅ **Phase 1:** Authentication & Job Scraping
- 📋 **Phase 2:** Resume matching (planned)
- 💾 **Phase 3:** Job management (planned)
- 🤖 **Phase 4:** Auto-apply (planned)

## 📚 Documentation

See `docs/` folder for detailed specifications

## 🔒 Security

- Never commit your `.env` file
- Credentials stored locally only
- Session files are gitignored

---

**🪿 Let's help you land that dream co-op!**
