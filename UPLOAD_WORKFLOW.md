# 📤 Cover Letter Upload Workflow

## Overview
The upload system now tracks which cover letters have been uploaded to WaterlooWorks, preventing duplicates.

## Quick Commands

### Generate New Cover Letters
```powershell
python main.py --mode cover-letter
```
- Generates cover letters for jobs in `data/jobs_scraped.json`
- Skips jobs that already have cover letters
- Saves PDFs to `cover_letters/`

### Upload ONLY New Cover Letters
```powershell
python main.py --mode upload-covers
```
- **Only uploads files NOT in `data/uploaded_cover_letters.json`**
- Automatically tracks each successful upload
- Shows stats: Total, Uploaded, Skipped, Failed

### Mark Existing Cover Letters as Uploaded
```powershell
python sync_uploaded_covers.py
```
- **Use this if you've already manually uploaded some cover letters**
- Adds all existing PDFs to the tracking file
- Prevents re-uploading duplicates

## How It Works

### Tracking File
Location: `data/uploaded_cover_letters.json`

Example:
```json
{
  "uploaded_files": [
    "Company_A_Job_Title.pdf",
    "Company_B_Job_Title.pdf"
  ]
}
```

### Upload Flow
1. ✅ Scan `cover_letters/` directory for PDFs
2. 📂 Load `data/uploaded_cover_letters.json`
3. 🔍 Filter: Only upload files **NOT** in tracking file
4. 📤 Upload each new file to WaterlooWorks
5. ✅ Add successfully uploaded files to tracking

### What You Just Did
```
✅ Generated 14 NEW cover letters (from 135 Geese jobs)
✅ Already had 121 cover letters (skipped generation)
✅ Ran sync script → Marked all 155 existing PDFs as "uploaded"
```

**Result:** Next `upload-covers` run will skip all 155 and only upload brand new ones! 🎉

## Scenarios

### Scenario 1: Fresh Start (All Cover Letters Generated)
```powershell
# Generate all
python main.py --mode cover-letter

# Mark as uploaded (don't actually upload yet)
python sync_uploaded_covers.py

# Later: Upload only newly generated ones
python main.py --mode upload-covers
```

### Scenario 2: Need to Re-upload Everything
```powershell
# Delete tracking file
Remove-Item data/uploaded_cover_letters.json

# Upload all
python main.py --mode upload-covers
```

### Scenario 3: Added New Jobs to Geese
```powershell
# Generate cover letters (only new jobs)
python main.py --mode cover-letter

# Upload (only new ones)
python main.py --mode upload-covers
```

## Clearing Caches

### Clear Upload Tracking Only
```powershell
Remove-Item data/uploaded_cover_letters.json
```

### Clear All Caches (including upload tracking)
```powershell
python modules/clear_cache.py
```

## Tips

✅ **Run `sync_uploaded_covers.py` after manually uploading** to keep tracking in sync

✅ **Safe to run `upload-covers` multiple times** - won't duplicate uploads

✅ **Delete `uploaded_cover_letters.json` if WaterlooWorks lost your uploads** and you need to re-upload

✅ **Check stats after upload** to verify success/failure counts
