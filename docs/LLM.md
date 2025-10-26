# LLM Integration Guide

## Overview

The system uses LLMs (Gemini/OpenAI) for intelligent job analysis and cover letter generation.

---

## Features

### 1. Cover Letter Generation
- Analyzes job descriptions and resume
- Generates personalized, role-specific cover letters
- Saves as Word docs and converts to PDF
- Uses evidence-based approach (no hallucinations)

### 2. Compensation Extraction
- Extracts salary/pay info from job descriptions
- Handles various formats (hourly, annual, ranges)
- Normalizes to consistent format

### 3. Job Requirement Analysis
- Categorizes requirements (technical, soft skills, nice-to-have)
- Identifies external applications and document requirements
- Detects bonus items (portfolios, GitHub, etc.)

---

## Configuration

Add to `.env`:
```env
# Use one of these:
GOOGLE_API_KEY=your_gemini_key     # Recommended (Gemini 2.0 Flash)
OPENAI_API_KEY=your_openai_key     # Alternative
```

Set provider in `config.json`:
```json
{
  "llm": {
    "provider": "gemini",           // or "openai"
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

---

## Usage

### Generate Cover Letters
```bash
# For all jobs in a folder
python main.py --mode generate-folder-covers --waterlooworks-folder "FOLDER_NAME"

# For specific jobs
python main.py --mode cover-letter
```

### Analyze Job Requirements
```bash
python analyze_concise.py
```

---

## How It Works

### Cover Letter Generation
1. **Extract Context**: Job description + resume bullets
2. **LLM Prompt**: Generates tailored letter matching job requirements
3. **Format**: Saves as .docx, converts to PDF
4. **Validation**: Checks for generic phrases, ensures personalization

### Evidence-Based Approach
- Only uses **matched resume bullets** as evidence
- No full resume sent to LLM (prevents hallucinations)
- Focuses on specific job-resume alignment

---

## Best Practices

✅ **Do:**
- Review generated cover letters before submission
- Adjust temperature (0.7-0.9) for different tones
- Use specific job requirements for better results

❌ **Don't:**
- Submit without reviewing
- Use default prompts for highly specialized roles
- Exceed API rate limits (add delays for batch processing)

---

## Cost

- **Gemini 2.0 Flash**: Free tier (15 RPM, 1M TPM)
- **OpenAI GPT-3.5**: ~$0.002 per cover letter
- **OpenAI GPT-4**: ~$0.03 per cover letter

Recommended: Use Gemini for cost-free operation.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Add key to `.env` file |
| Generic cover letters | Lower temperature, improve job description quality |
| Rate limit errors | Add delays between requests |
| PDF conversion fails | Check if `pywin32` is installed (Windows only) |

---

## Future Enhancements

- Multi-language support
- Custom tone/style profiles
- A/B testing for different approaches
- Interview preparation insights
