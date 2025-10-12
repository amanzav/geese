"""
Script to remove field prefixes from existing jobs_scraped.json
Removes prefixes like "Job Summary:", "Required Skills:", etc.
"""

import json

def clean_prefix(text, prefix):
    """Remove prefix from text if it starts with it"""
    if isinstance(text, str) and text.startswith(prefix):
        return text.replace(prefix, "", 1).strip()
    return text

def main():
    # Load existing jobs
    with open('data/jobs_scraped.json', 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"Cleaning {len(jobs)} jobs...")
    
    # Clean each job
    prefixes = {
        "summary": "Job Summary:",
        "responsibilities": "Job Responsibilities:",
        "skills": "Required Skills:",
        "additional_info": "Additional Application Information:",
        "employment_location_arrangement": "Employment Location Arrangement:",
        "work_term_duration": "Work Term Duration:"
    }
    
    for job in jobs:
        for field, prefix in prefixes.items():
            if field in job:
                job[field] = clean_prefix(job[field], prefix)
    
    # Save cleaned jobs
    with open('data/jobs_scraped.json', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cleaned {len(jobs)} jobs")
    print("✓ Removed field prefixes (Job Summary:, Required Skills:, etc.)")

if __name__ == "__main__":
    main()
