# 🪿 Geese - WaterlooWorks Automation

AI-powered automation tool for University of Waterloo co-op students to streamline their WaterlooWorks job application process.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install browser driver (if using Playwright)
playwright install chromium
```

### 2. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# WATERLOOWORKS_USERNAME=your_username
# WATERLOOWORKS_PASSWORD=your_password
```

### 3. Test Login

```bash
# Run the login test
python test_login.py
```

## 📁 Project Structure

```
geese/
├── modules/           # Core modules
│   ├── auth.py       # ✅ Authentication (Phase 1)
│   ├── scraper.py    # 🔄 Job scraping (Phase 1)
│   ├── matcher.py    # 📋 Resume matching (Phase 2)
│   ├── saver.py      # 💾 Save jobs (Phase 3)
│   └── applicator.py # 🤖 Auto-apply (Phase 4)
├── data/             # Scraped data & sessions
├── saved_jobs/       # Saved job listings
├── input/            # Your resume
└── logs/             # Application logs
```

## 📝 Development Status

- ✅ **Phase 1a:** Authentication module
- 🔄 **Phase 1b:** Job scraping (next)
- 📋 **Phase 2:** Resume matching
- 💾 **Phase 3:** Job management
- 🤖 **Phase 4:** Auto-apply

## 📚 Documentation

- See `MVP.md` for detailed MVP specification
- See `PRD.md` for full product requirements

## 🔒 Security

- Never commit your `.env` file
- Credentials stored locally only
- Session files are gitignored

## 📄 License

MIT - Built for University of Waterloo co-op students

---

**🪿 Let's help you land that dream co-op!**
