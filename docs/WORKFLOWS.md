# Folder-Specific Workflow Guide

This guide shows how to scrape, generate cover letters, and apply to jobs from any WaterlooWorks folder.

## 📋 Complete Workflow

### Step 1: Scrape Jobs from Folder
Scrape all jobs from a specific WaterlooWorks folder with AI-powered requirement analysis.

```bash
python main.py --mode scrape-folder --waterlooworks-folder "FOLDER_NAME"
```

**Example:**
```bash
python main.py --mode scrape-folder --waterlooworks-folder "good shit"
```

**Output:**
- Creates `data/jobs_FOLDER_NAME.json` with all job details
- Includes requirement categorization:
  - External applications (with URLs)
  - Extra documents needed
  - Bonus items available

---

### Step 2: Generate Cover Letters
Generate personalized cover letters for all jobs in the folder.

```bash
python main.py --mode generate-folder-covers --waterlooworks-folder "FOLDER_NAME"
```

**Example:**
```bash
python main.py --mode generate-folder-covers --waterlooworks-folder "good shit"
```

**Features:**
- ✅ Skips already-generated cover letters
- ✅ Retry logic (up to 3 attempts for failed generations)
- ✅ Sanitized filenames (no illegal characters)
- ✅ Saves PDFs to `cover_letters/` folder

**Output:**
- One PDF per job in `cover_letters/`
- Summary statistics (generated, skipped, failed)

---

### Step 3: Generate Job Summary (Optional)
Create a markdown summary with pay, location, and requirements.

```bash
python generate_job_summary.py
```

**Output:**
- Creates `data/jobs_FOLDER_NAME_summary.md`
- Organized by requirement type:
  - 🔗 External applications
  - 📎 Extra documents
  - ⭐ Bonus items
  - ✅ Standard applications

---

### Step 4: Apply to Jobs
Automatically apply to all standard jobs in the folder.

```bash
python main.py --mode apply --waterlooworks-folder "FOLDER_NAME" --max-apps 50
```

**Example:**
```bash
python main.py --mode apply --waterlooworks-folder "good shit" --max-apps 50
```

**Optional Flags:**
- `--max-apps N` - Maximum number of applications (default: 10)
- `--skip-prescreening` - Skip jobs with pre-screening questions

**What it does:**
- ✅ Navigates to your specified folder on WaterlooWorks
- ✅ Matches jobs with generated cover letters
- ✅ Uploads cover letters and applies automatically
- ⏭️ Skips jobs requiring external applications
- ⏭️ Skips jobs requiring extra documents
- ⏭️ Skips jobs with pre-screening questions (if flag set)
- 📊 Generates detailed application report

**Output:**
- Console summary with statistics
- `data/application_report_TIMESTAMP.md` with details

---

## 🎯 Example: "good shit" Folder

Complete workflow for the "good shit" folder:

```bash
# 1. Scrape the folder (55 jobs)
python main.py --mode scrape-folder --waterlooworks-folder "good shit"

# 2. Generate cover letters (55 PDFs)
python main.py --mode generate-folder-covers --waterlooworks-folder "good shit"

# 3. Generate summary (optional)
python generate_job_summary.py

# 4. Review summary to see job categories
# Open: data/jobs_good_shit_summary.md

# 5. Apply to standard jobs
python main.py --mode apply --waterlooworks-folder "good shit" --max-apps 50

# 6. Review application report
# Open: data/application_report_TIMESTAMP.md
```

---

## 📊 Expected Results

From the "good shit" folder (55 jobs total):

- **38 Standard Applications** → Will apply automatically ✅
- **8 External Applications** → Skipped (apply manually with provided URLs) 🔗
- **2 Extra Documents** → Skipped (need transcripts, portfolios, etc.) 📎
- **7 Bonus Items** → Applies, but you may want to add bonus items manually ⭐

---

## 🔍 Troubleshooting

### "No jobs found" error
**Solution:** Run scrape-folder mode first
```bash
python main.py --mode scrape-folder --waterlooworks-folder "FOLDER_NAME"
```

### "Missing cover letter" warnings
**Solution:** Run generate-folder-covers mode first
```bash
python main.py --mode generate-folder-covers --waterlooworks-folder "FOLDER_NAME"
```

### Folder name with spaces
**Always use quotes:**
```bash
python main.py --mode apply --waterlooworks-folder "good shit"
```

### Jobs with external applications
These are skipped automatically. Check the application report for URLs and apply manually.

### Jobs requiring extra documents
These are skipped automatically. Upload documents manually on WaterlooWorks, then apply.

---

## 💡 Tips

1. **Review the summary first** - Use `generate_job_summary.py` to understand job categories before applying
2. **Start small** - Use `--max-apps 5` first to test the workflow
3. **Check application report** - Review `data/application_report_TIMESTAMP.md` for jobs that need manual attention
4. **Handle external apps separately** - Note jobs requiring external applications and apply through provided URLs
5. **Upload bonus items** - For jobs with bonus items, consider uploading GitHub/portfolio links manually after auto-application

---

## 📁 File Structure

```
waterloo_works_automator/
├── data/
│   ├── jobs_good_shit.json          # Scraped jobs
│   ├── jobs_good_shit_summary.md    # Summary report
│   └── application_report_*.md      # Application results
├── cover_letters/
│   ├── Company_Job_Title.pdf        # Generated cover letters
│   └── ...
└── main.py                           # Main script
```

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Scrape folder | `python main.py --mode scrape-folder --waterlooworks-folder "NAME"` |
| Generate covers | `python main.py --mode generate-folder-covers --waterlooworks-folder "NAME"` |
| Generate summary | `python generate_job_summary.py` |
| Apply to jobs | `python main.py --mode apply --waterlooworks-folder "NAME" --max-apps 50` |
| Skip pre-screening | Add `--skip-prescreening` flag to apply command |
