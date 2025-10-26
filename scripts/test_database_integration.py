"""
Test script to verify database integration with scraper and matcher
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import get_db

def test_database_integration():
    """Test that database modules are working correctly"""
    print("🧪 Testing Database Integration\n")
    print("="*60)
    
    # Test 1: Database connection
    print("\n1️⃣  Testing database connection...")
    try:
        db = get_db()
        print("   ✅ Database connection successful")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Test 2: Get stats
    print("\n2️⃣  Testing database stats...")
    try:
        stats = db.get_stats()
        print(f"   ✅ Stats retrieved:")
        for table, count in stats.items():
            print(f"      - {table}: {count} records")
    except Exception as e:
        print(f"   ❌ Stats retrieval failed: {e}")
        return False
    
    # Test 3: Get jobs
    print("\n3️⃣  Testing job retrieval...")
    try:
        jobs = db.get_all_jobs()
        print(f"   ✅ Retrieved {len(jobs)} jobs")
        if jobs:
            sample = jobs[0]
            print(f"      Sample job: {sample.get('title')} @ {sample.get('company')}")
    except Exception as e:
        print(f"   ❌ Job retrieval failed: {e}")
        return False
    
    # Test 4: Get matches
    print("\n4️⃣  Testing match retrieval...")
    try:
        matches = db.get_all_matches()
        print(f"   ✅ Retrieved {len(matches)} matches")
        if matches:
            sample_id = list(matches.keys())[0]
            sample = matches[sample_id]
            print(f"      Sample match: Score {sample.get('match_score')}, Decision: {sample.get('decision')}")
    except Exception as e:
        print(f"   ❌ Match retrieval failed: {e}")
        return False
    
    # Test 5: Test scraper import
    print("\n5️⃣  Testing scraper module import...")
    try:
        from modules.scraper import WaterlooWorksScraper
        print("   ✅ Scraper module imported successfully")
    except Exception as e:
        print(f"   ❌ Scraper import failed: {e}")
        return False
    
    # Test 6: Test matcher import
    print("\n6️⃣  Testing matcher module import...")
    try:
        from modules.matcher import ResumeMatcher
        print("   ✅ Matcher module imported successfully")
    except Exception as e:
        print(f"   ❌ Matcher import failed: {e}")
        return False
    
    # Test 7: Test matcher initialization
    print("\n7️⃣  Testing matcher initialization with database...")
    try:
        matcher = ResumeMatcher(use_database=True)
        print(f"   ✅ Matcher initialized with {len(matcher.match_cache)} cached matches")
    except Exception as e:
        print(f"   ❌ Matcher initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ All tests passed!\n")
    return True

if __name__ == "__main__":
    success = test_database_integration()
    exit(0 if success else 1)
