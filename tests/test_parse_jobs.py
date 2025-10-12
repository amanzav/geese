"""
Test script for job parsing functionality
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper


def print_job(job, detailed=False):
    """Pretty print a job"""
    print(f"  ID: {job.get('id')}")
    print(f"  Title: {job.get('title')}")
    print(f"  Company: {job.get('company')}")
    print(f"  Division: {job.get('division')}")
    print(f"  City: {job.get('city')}")
    print(f"  Level: {job.get('level')}")
    print(f"  Openings: {job.get('openings')}")
    print(f"  Applications: {job.get('applications')}")
    print(f"  Chances: {job.get('chances')}")
    print(f"  Deadline: {job.get('deadline')}")
    
    if detailed:
        print(f"\n  Summary:\n  {job.get('summary', 'N/A')}")
        print(f"\n  Responsibilities:\n  {job.get('responsibilities', 'N/A')}")
        print(f"\n  Skills:\n  {job.get('skills', 'N/A')}")
        print(f"\n  Additional Info:\n  {job.get('additional_info', 'N/A')}")
    print()


def main():
    print("🪿 Geese - Job Parser Test\n")
    
    # Load credentials
    load_dotenv()
    username = os.getenv("WATERLOOWORKS_USERNAME")
    password = os.getenv("WATERLOOWORKS_PASSWORD")
    
    if not username or not password:
        print("❌ ERROR: Add credentials to .env file")
        return
    
    auth = WaterlooWorksAuth(username, password)
    
    try:
        # Login
        auth.login()
        
        # Create scraper and navigate
        scraper = WaterlooWorksScraper(auth.driver)
        scraper.go_to_jobs_page(program_filter_value="38688")
        
        # Test 1: Scrape first page (basic info only)
        print("\n" + "="*60)
        print("TEST 1: Basic scraping (no details)")
        print("="*60 + "\n")
        
        jobs = scraper.scrape_current_page(include_details=False)
        
        print("First 3 jobs:\n")
        for i, job in enumerate(jobs[:3], 1):
            print(f"Job #{i}:")
            print_job(job)
        
        if len(jobs) > 3:
            print(f"... and {len(jobs) - 3} more jobs\n")
        
        # Test 2: Get full details for first job
        print("\n" + "="*60)
        print("TEST 2: Detailed scraping (with descriptions)")
        print("="*60 + "\n")
        
        if jobs:
            rows = scraper.get_job_table()
            first_job = scraper.parse_job_row(rows[0])
            detailed_job = scraper.get_job_details(first_job)
            
            print(f"Full details for: {detailed_job.get('title')}\n")
            print_job(detailed_job, detailed=True)
        
        # Save sample
        os.makedirs("data", exist_ok=True)
        with open("data/jobs_sample.json", 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print("💾 Saved sample to: data/jobs_sample.json")
        
        # Keep browser open
        print("\n👀 Keeping browser open for 15 seconds...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        auth.close()
        print("✅ Test complete!")


if __name__ == "__main__":
    main()
