# Custom Folders - Quick Reference

## New Command-Line Options

You can now customize which folders the system uses for resumes, cover letters, and WaterlooWorks folders!

### Options Added:
```bash
--input-folder INPUT_FOLDER
    Folder containing resume (default: input/)

--cover-letters-folder COVER_LETTERS_FOLDER
    Folder to save/read cover letters (default: cover_letters/)

--waterlooworks-folder WATERLOOWORKS_FOLDER
    WaterlooWorks folder name to save jobs to (default: from config.json)
```

## Quick Examples

### 1. Generate covers from different resume folder
```bash
python main.py --mode cover-letter \
  --input-folder "resumes/tech" \
  --cover-letters-folder "covers_tech"
```

### 2. Apply with covers from different folder
```bash
python main.py --mode apply --max-apps 20 \
  --cover-letters-folder "covers_backup" \
  --waterlooworks-folder "software-jobs"
```

### 3. Scrape and save to different WaterlooWorks folder
```bash
python main.py --mode realtime \
  --waterlooworks-folder "data-science"
```

### 4. Upload covers from alternative folder
```bash
python main.py --mode upload-covers \
  --cover-letters-folder "covers_v2"
```

## Use Case: Multiple Job Types

If you have different resumes for different job categories:

```bash
# Software jobs
python main.py --mode cover-letter \
  --input-folder "resumes/software" \
  --cover-letters-folder "covers_software" \
  --waterlooworks-folder "software"

# Hardware jobs  
python main.py --mode cover-letter \
  --input-folder "resumes/hardware" \
  --cover-letters-folder "covers_hardware" \
  --waterlooworks-folder "hardware"

# Then apply separately
python main.py --mode apply --max-apps 15 \
  --cover-letters-folder "covers_software" \
  --waterlooworks-folder "software"
```

## Default Behavior (No Options)

If you don't specify any options, the system uses:
- `input/resume.pdf` - Your resume
- `cover_letters/` - Cover letter storage
- `geese` (or from config.json) - WaterlooWorks folder

## Where This Helps

✅ Test different versions without overwriting
✅ Organize by job category (software, hardware, research)
✅ Use different resumes for different applications
✅ Backup and version control of cover letters
✅ Separate folders for different WaterlooWorks categories

See `docs/CUSTOM_FOLDERS.md` for detailed examples and workflows!
