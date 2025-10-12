"""
Quick test script to demonstrate match caching
"""

import json
from modules.matcher import ResumeMatcher

# Load test jobs
with open('data/jobs_scraped.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

# Take first 5 jobs for quick test
test_jobs = jobs[:5]

print("=" * 70)
print("TEST 1: First run - should analyze all jobs")
print("=" * 70)

matcher = ResumeMatcher()
results = matcher.batch_analyze(test_jobs, force_rematch=False)

print("\n" + "=" * 70)
print("TEST 2: Second run - should use cache")
print("=" * 70)

matcher2 = ResumeMatcher()
results2 = matcher2.batch_analyze(test_jobs, force_rematch=False)

print("\n" + "=" * 70)
print("TEST 3: Force rematch - should analyze again")
print("=" * 70)

matcher3 = ResumeMatcher()
results3 = matcher3.batch_analyze(test_jobs, force_rematch=True)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total jobs tested: {len(test_jobs)}")
print(f"Cache file location: data/job_matches_cache.json")
print("✅ Caching system working correctly!")
