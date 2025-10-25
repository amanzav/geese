# Using Custom Folders

By default, the system uses these folders:
- `input/` - Contains your resume
- `cover_letters/` - Stores generated cover letters
- `geese` - WaterlooWorks folder name (from config.json)

You can now override these with command-line options!

## Command-Line Options

### `--input-folder`
Specify where to read your resume from
```bash
python main.py --mode cover-letter --input-folder "resumes/software"
```

### `--cover-letters-folder`
Specify where to save/read cover letters
```bash
python main.py --mode cover-letter --cover-letters-folder "covers_tech"
```

### `--waterlooworks-folder`
Specify which WaterlooWorks folder to use
```bash
python main.py --mode realtime --waterlooworks-folder "software-jobs"
```

## Complete Examples

### Example 1: Use different resume for hardware jobs
```bash
python main.py --mode cover-letter \
  --input-folder "resumes/hardware" \
  --cover-letters-folder "covers_hardware" \
  --waterlooworks-folder "hardware"
```

### Example 2: Generate covers from alternative resume folder
```bash
python main.py --mode cover-letter \
  --input-folder "input/alternative" \
  --cover-letters-folder "covers_startup"
```

### Example 3: Apply to jobs from different folder
```bash
python main.py --mode apply \
  --max-apps 20 \
  --cover-letters-folder "covers_tech" \
  --waterlooworks-folder "software-engineering"
```

### Example 4: Upload covers from different folder
```bash
python main.py --mode upload-covers \
  --cover-letters-folder "covers_backup"
```

## Typical Workflow

### Scenario: You have different resumes for different job types

1. **Organize your folders:**
   ```
   resumes/
     ├── software/
     │   └── resume.pdf
     └── hardware/
         └── resume.pdf
   
   covers_software/
   covers_hardware/
   ```

2. **Generate software covers:**
   ```bash
   python main.py --mode cover-letter \
     --input-folder "resumes/software" \
     --cover-letters-folder "covers_software" \
     --waterlooworks-folder "software"
   ```

3. **Generate hardware covers:**
   ```bash
   python main.py --mode cover-letter \
     --input-folder "resumes/hardware" \
     --cover-letters-folder "covers_hardware" \
     --waterlooworks-folder "hardware"
   ```

4. **Apply to software jobs:**
   ```bash
   python main.py --mode apply \
     --max-apps 25 \
     --cover-letters-folder "covers_software" \
     --waterlooworks-folder "software"
   ```

5. **Apply to hardware jobs:**
   ```bash
   python main.py --mode apply \
     --max-apps 15 \
     --cover-letters-folder "covers_hardware" \
     --waterlooworks-folder "hardware"
   ```

## Tips

### 1. Keep resumes named consistently
Always name your resume `resume.pdf` in each folder, or update `config.json`:
```json
{
  "resume_path": "resumes/software/my_resume.pdf"
}
```

### 2. Folder structure recommendation
```
project/
  ├── resumes/
  │   ├── software/resume.pdf
  │   ├── hardware/resume.pdf
  │   └── research/resume.pdf
  ├── covers_software/
  ├── covers_hardware/
  ├── covers_research/
  └── data/
      └── jobs_scraped.json
```

### 3. Use config.json for permanent changes
For your primary setup, update `config.json`:
```json
{
  "resume_path": "resumes/software/resume.pdf",
  "waterlooworks_folder": "software"
}
```

Then use command-line options only when you need to switch.

## Common Use Cases

### Use Case 1: Testing with backup folders
Don't want to overwrite your main covers? Use a test folder:
```bash
python main.py --mode cover-letter \
  --cover-letters-folder "covers_test"
```

### Use Case 2: Different cover styles
Generate two sets of covers with different tones:
```bash
# Formal style
python main.py --mode cover-letter --cover-letters-folder "covers_formal"

# Casual style (after updating prompt in config)
python main.py --mode cover-letter --cover-letters-folder "covers_casual"
```

### Use Case 3: Multiple WaterlooWorks folders
Organize jobs by category:
- `software` folder for dev jobs
- `data-science` folder for ML/AI jobs
- `startup` folder for startup jobs

```bash
# Scrape and save to software folder
python main.py --mode realtime --waterlooworks-folder "software"

# Scrape and save to data-science folder
python main.py --mode realtime --waterlooworks-folder "data-science"
```

## Notes

- All paths are relative to the project root directory
- Folders will be created automatically if they don't exist
- The system will always look for `resume.pdf` in your input folder
- Cover letter naming convention remains the same: `{Company}_{Title}.pdf`
