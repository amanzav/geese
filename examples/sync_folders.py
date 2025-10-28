"""
Example: Run folder sync to collect all folders and jobs
This demonstrates how to use the FolderSync module
"""

import sys
from modules.auth import login_with_credentials
from modules.scraper import WaterlooWorksScraper
from modules.folder_sync import FolderSync


def main():
    """Main function to demonstrate folder sync"""
    print("=" * 60)
    print("WATERLOOWORKS FOLDER SYNC")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1️⃣  Logging in to WaterlooWorks...")
    driver = login_with_credentials()
    
    if not driver:
        print("❌ Login failed. Exiting.")
        return
    
    print("✅ Login successful!")
    
    # Step 2: Initialize scraper (needed for detailed job scraping)
    print("\n2️⃣  Initializing scraper...")
    scraper = WaterlooWorksScraper(driver, use_supabase=True)
    
    # Step 3: Initialize folder sync
    print("\n3️⃣  Initializing folder sync...")
    folder_sync = FolderSync(driver, scraper=scraper, use_supabase=True)
    
    # Step 4: Run the sync
    print("\n4️⃣  Starting folder sync...")
    print("     This will:")
    print("     • Find all your WaterlooWorks folders")
    print("     • Extract job IDs from each folder")
    print("     • Sync missing jobs to Supabase")
    print("     • Save folder-job mappings to data/user_folders.json")
    print()
    
    try:
        folders = folder_sync.sync_all_folders()
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 SYNC RESULTS")
        print("=" * 60)
        
        if folders:
            for folder_name, job_ids in folders.items():
                print(f"\n📁 {folder_name}")
                print(f"   Jobs: {len(job_ids)}")
                if job_ids:
                    print(f"   Sample IDs: {', '.join(job_ids[:5])}")
                    if len(job_ids) > 5:
                        print(f"   ... and {len(job_ids) - 5} more")
        else:
            print("⚠️  No folders found")
        
        print("\n" + "=" * 60)
        print("✅ Sync complete! Data saved to data/user_folders.json")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the browser
        print("\n5️⃣  Closing browser...")
        try:
            driver.quit()
            print("✅ Browser closed")
        except Exception as e:
            print(f"⚠️  Error closing browser: {e}")


if __name__ == "__main__":
    main()
