# 🔔 Manual Intervention Scenarios

The automation now alerts you with a **beep sound** and **keeps the tab open** for manual completion in these scenarios:

## 1. Pre-Screening Questions (if not skipping)
**What happens:**
- 🔔 Plays beep sound (1000 Hz, 500ms)
- ⏸️ Automation pauses
- 📋 Tab stays open for you to answer questions
- ⏳ Waits for you to close the tab manually
- ✅ Continues to next job after tab is closed

**Console message:**
```
      🔔 BEEP! Pre-screening detected - complete manually
      ⏳ Waiting for you to close the tab manually...
```

**To skip these automatically instead:**
```powershell
python main.py --mode apply --max-apps 50 --skip-prescreening
```

## 2. Missing Cover Letter
**What happens:**
- 🔔 Plays beep sound (1000 Hz, 500ms)
- ⏸️ Automation pauses
- 📋 Tab stays open for you to complete application
- ⏳ Waits for you to close the tab manually
- ✅ Continues to next job after tab is closed

**Console message:**
```
      🔔 BEEP! Cover letter missing - complete manually
      ⏳ Waiting for you to close the tab manually...
```

**What to do:**
1. Upload the missing cover letter (if needed)
2. Complete the application form
3. Submit the application
4. Close the tab
5. Automation continues automatically ✅

## Automated Scenarios (No Manual Intervention)

### ✅ Jobs that auto-apply successfully:
- Has cover letter ✓
- No pre-screening ✓
- No extra documents required ✓

**Console message:**
```
      ✓ Clicked Submit button
      ✓ Closed tab and returned to job list
```

### ⏭️ Jobs that are auto-skipped:
- Requires extra documents (transcripts, portfolios, etc.)
- Pre-screening detected (with `--skip-prescreening` flag)

**Console message:**
```
      ⏭️  Skipping - requires additional documents
      ✓ Closed tab and returned to job list
```

## How to Use

### Standard Mode (Beep on Manual Tasks)
```powershell
python main.py --mode apply --max-apps 50
```
- Beeps and pauses for pre-screening ✓
- Beeps and pauses for missing cover letters ✓
- Auto-submits when everything is ready ✓

### Skip Pre-Screening Mode
```powershell
python main.py --mode apply --max-apps 50 --skip-prescreening
```
- Skips jobs with pre-screening (silent) ✓
- Beeps and pauses for missing cover letters ✓
- Auto-submits when everything is ready ✓

## Sound Settings

**Beep Frequency:** 1000 Hz  
**Beep Duration:** 500ms (0.5 seconds)  
**Platform:** Windows (uses `winsound` module)

If you want to adjust the beep:
- **Higher pitch:** Increase frequency (e.g., 1500 Hz)
- **Longer beep:** Increase duration (e.g., 1000ms)
- **Multiple beeps:** Add multiple `winsound.Beep()` calls

## Workflow Example

```
[1/135] Company A - Software Developer
      ✓ Clicked Apply button
      ✓ Switched to new tab
      ✓ No pre-screening
      ✓ Created custom package
      ✓ Selected resume
      ⏳ Selecting cover letter: Company_A_Software_Developer
      ✓ Clicked modal Select button
      ✓ Clicked Submit button
      ✓ Closed tab and returned to job list

[2/135] Company B - ML Engineer
      ✓ Clicked Apply button
      ✓ Switched to new tab
      ✓ No pre-screening
      ✓ Created custom package
      ✓ Selected resume
      ⚠️  Cover letter not found: Company_B_ML_Engineer
      🔔 BEEP! Cover letter missing - complete manually
      ⏳ Waiting for you to close the tab manually...
      [YOU: Upload cover letter, submit, close tab]
      ✓ Tab closed, continuing...

[3/135] Company C - Data Analyst
      ✓ Clicked Apply button
      ✓ Switched to new tab
      🔔 BEEP! Pre-screening detected - complete manually
      ⏳ Waiting for you to close the tab manually...
      [YOU: Answer questions, submit, close tab]
      ✓ Tab closed, continuing...
```

## Tips

✅ **Keep the terminal visible** so you can see when automation pauses

✅ **Listen for beeps** to know when manual action is needed

✅ **Don't minimize the browser** - automation needs to interact with it

✅ **Close tabs when done** - automation waits for you to close before continuing

✅ **Review the final report** - shows all skipped/failed jobs with links to apply manually later
