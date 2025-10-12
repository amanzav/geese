"""
Test script for auto-save to WaterlooWorks folder functionality
"""

import sys
import os
import time
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper


def test_save_to_folder():
    """Test saving a job to WaterlooWorks folder"""
    
    print("=" * 70)
    print("🧪 TEST: Save Job to WaterlooWorks Folder")
    print("=" * 70)
    print()
    
    # Get credentials
    print("🔐 Enter your WaterlooWorks credentials")
    username = input("Username (UW email): ").strip()
    password = getpass.getpass("Password: ")
    print()
    
    # Login
    print("🔑 Logging in...")
    auth = WaterlooWorksAuth(username, password)
    auth.login()
    print("✅ Login successful\n")
    
    # Create scraper
    scraper = WaterlooWorksScraper(auth.driver)
    scraper.go_to_jobs_page()
    
    # Get first job from the list
    print("📊 Getting first job from list...")
    rows = scraper.get_job_table()
    
    if not rows:
        print("❌ No jobs found")
        auth.close()
        return
    
    # Parse first job
    job_data = scraper.parse_job_row(rows[0])
    print(f"✅ Found job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'N/A')}\n")
    
    # Test save functionality
    folder_name = input("Enter folder name to save to (default: geese): ").strip() or "geese"
    print()
    
    print(f"💾 Attempting to save job to '{folder_name}' folder...")
    success = scraper.save_job_to_folder(job_data, folder_name=folder_name)
    
    if success:
        print("\n✅ TEST PASSED: Job saved successfully!")
    else:
        print("\n❌ TEST FAILED: Could not save job")
    
    # Wait a bit to see the result
    print("\nWaiting 3 seconds before closing...")
    time.sleep(3)
    
    # Close browser
    auth.close()
    print("🚪 Browser closed")


if __name__ == "__main__":
    try:
        test_save_to_folder()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
