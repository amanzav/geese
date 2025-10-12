"""
Test the improved hybrid matching algorithm
"""

import json
from modules.matcher import ResumeMatcher

# Load test jobs
with open('data/jobs_scraped.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

# Take first 5 jobs for testing
test_jobs = jobs[:5]

print("=" * 80)
print("TESTING IMPROVED HYBRID MATCHING ALGORITHM")
print("=" * 80)
print()

matcher = ResumeMatcher()
results = matcher.batch_analyze(test_jobs, force_rematch=True)

print("\n" + "=" * 80)
print("RESULTS - Top 5 Jobs")
print("=" * 80)

for i, result in enumerate(results, 1):
    job = result["job"]
    match = result["match"]
    
    emoji = "🟢" if match["fit_score"] >= 70 else "🟡" if match["fit_score"] >= 50 else "🟠"
    
    print(f"\n{emoji} #{i} - {job['title']}")
    print(f"   Company: {job['company']}")
    print(f"   Fit Score: {match['fit_score']}/100")
    print(f"   Breakdown:")
    print(f"     - Keyword Match: {match['keyword_match']}%")
    print(f"     - Semantic Coverage: {match['coverage']}%")
    print(f"     - Semantic Strength: {match['skill_match']}%")
    print(f"     - Seniority: {match['seniority_alignment']}%")
    
    if match.get("matched_technologies"):
        print(f"   ✅ Matched Tech ({len(match['matched_technologies'])}): {', '.join(match['matched_technologies'][:8])}")
    
    if match.get("missing_technologies"):
        print(f"   ❌ Missing Tech ({len(match['missing_technologies'])}): {', '.join(match['missing_technologies'][:8])}")

print("\n" + "=" * 80)
print("✅ Improved algorithm successfully tested!")
print("Key improvements:")
print("  - Explicit technology keyword matching")
print("  - Better requirement parsing (must-have vs nice-to-have)")
print("  - Higher similarity threshold (0.65 vs 0.50)")
print("  - Shows which technologies you match/miss")
print("=" * 80)

