"""
Test script for job scraping functionality
"""

import os
import sys
import time
import traceback
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper


def main():
    print("🪿 Geese - Job Scraper Test\n")
    
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
        
        # Create scraper
        scraper = WaterlooWorksScraper(auth.driver)
        
        # Navigate to jobs page with program filter
        # Change "38688" to your program's filter value
        scraper.go_to_jobs_page(program_filter_value="38688")
        
        # Check pagination
        try:
            num_pages = scraper.get_pagination_pages()
            print(f"📄 Total pages: {num_pages}")
        except Exception:
            print("📄 Single page (no pagination)")
            num_pages = 1
        
        # Scrape all pages
        all_jobs = []
        
        for page in range(1, num_pages + 1):
            print(f"\n🔍 Scanning page {page}/{num_pages}...")
            
            jobs = scraper.get_job_table()
            all_jobs.extend(jobs)
            
            # Print first few columns of each job
            for i, job_row in enumerate(jobs, 1):
                cells = job_row.find_elements("tag name", "td")
                if len(cells) >= 3:
                    print(f"  Job {i}: {cells[0].text} | {cells[1].text} | {cells[2].text}")
            
            # Go to next page
            if page < num_pages:
                print(f"\n➡️  Going to page {page + 1}...")
                scraper.next_page()
        
        print(f"\n✅ Total jobs found: {len(all_jobs)}")
        
        # Keep browser open
        print("\n👀 Keeping browser open for 15 seconds...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    finally:
        auth.close()
        print("✅ Test complete!")


if __name__ == "__main__":
    main()
