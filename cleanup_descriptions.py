"""
Quick script to clean up jobs_scraped.json:
- Remove duplicate 'description' fields
- Remove 'city' field (we use 'location' instead)
Run this once to clean up existing cached jobs
"""

import json

# Load existing jobs
with open("data/jobs_scraped.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Clean up each job
cleaned_jobs = []
for job in jobs:
    # Remove 'description' field if exists
    if "description" in job:
        del job["description"]
    
    # Ensure 'location' exists (convert from 'city' if needed)
    if "city" in job and "location" not in job:
        job["location"] = job["city"]
    
    # Remove 'city' field (we only use 'location')
    if "city" in job:
        del job["city"]
    
    cleaned_jobs.append(job)

# Save cleaned jobs
with open("data/jobs_scraped.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_jobs, f, indent=2, ensure_ascii=False)

print(f"✅ Cleaned {len(cleaned_jobs)} jobs")
print(f"   ✓ Removed redundant 'description' fields")
print(f"   ✓ Removed 'city' field (using 'location' only)")
print(f"   Jobs now use: location (not city)")
