"""
Folder Sync Module - Syncs WaterlooWorks folders and their job IDs
"""

import json
import os
import time
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .utils import (
    TIMEOUT, SELECTORS, WaitTimes,
    navigate_to_folder, get_pagination_pages, go_to_next_page,
    get_jobs_from_page, smart_page_wait
)
from .supabase_client import SupabaseClient


class FolderSync:
    """Syncs WaterlooWorks folders and ensures all jobs are in Supabase"""
    
    def __init__(self, driver, scraper=None, use_supabase=True):
        """
        Args:
            driver: Selenium WebDriver instance
            scraper: Optional WaterlooWorksScraper instance for detailed job scraping
            use_supabase: Whether to sync jobs to Supabase
        """
        self.driver = driver
        self.scraper = scraper
        self.use_supabase = use_supabase
        self.supabase = SupabaseClient() if use_supabase else None
        self.folders_file = os.path.join("data", "user_folders.json")
        
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def _load_folders(self) -> Dict[str, List[str]]:
        """Load existing folders from JSON file"""
        if os.path.exists(self.folders_file):
            try:
                with open(self.folders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"   ⚠️  Could not load folders file: {e}")
        return {}
    
    def _save_folders(self, folders: Dict[str, List[str]]):
        """Save folders to JSON file"""
        self._ensure_data_dir()
        try:
            with open(self.folders_file, 'w', encoding='utf-8') as f:
                json.dump(folders, f, indent=2)
            print(f"   ✓ Saved folders to {self.folders_file}")
        except Exception as e:
            print(f"   ✗ Could not save folders: {e}")
    
    def _get_all_folder_cards(self) -> List[tuple]:
        """
        Get all folder cards from the main page.
        Returns list of (folder_name, card_element) tuples.
        """
        try:
            print("   ⏳ Loading main page...")
            self.driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
            
            # Wait for page to load
            if not smart_page_wait(
                self.driver,
                (By.CSS_SELECTOR, ".margin--a--xxl"),
                max_wait=WaitTimes.SLOW
            ):
                print("   ✗ Main page did not load properly")
                return []
            
            # Navigate to the container with folders
            main_container = self.driver.find_element(By.CSS_SELECTOR, ".margin--a--xxl")
            
            # Find all margin--b--xxxl divs
            margin_divs = main_container.find_elements(By.CSS_SELECTOR, ".margin--b--xxxl")
            
            if len(margin_divs) < 3:
                print(f"   ⚠️  Expected at least 3 margin--b--xxxl divs, found {len(margin_divs)}")
                return []
            
            # Get the 3rd one (index 2)
            folders_container = margin_divs[2]
            
            # Get all stat cards (folders)
            stat_cards = folders_container.find_elements(By.CSS_SELECTOR, SELECTORS["stat_card"])
            
            if not stat_cards:
                print("   ⚠️  No folder cards found")
                return []
            
            # Exclude the last card (it's the "create folder" button)
            folder_cards = stat_cards[:-1] if len(stat_cards) > 1 else stat_cards
            
            folders = []
            for card in folder_cards:
                try:
                    # Extract folder name from the <a> tag's inner text
                    link = card.find_element(By.TAG_NAME, "a")
                    folder_name = link.text.strip()
                    
                    if folder_name:
                        folders.append((folder_name, card))
                        print(f"   ✓ Found folder: '{folder_name}'")
                except Exception as e:
                    print(f"   ⚠️  Could not extract folder name: {e}")
                    continue
            
            return folders
            
        except Exception as e:
            print(f"   ✗ Error getting folder cards: {e}")
            return []
    
    def _parse_job_ids_from_page(self) -> List[str]:
        """
        Extract just the job IDs from the current page.
        Simplified version of parse_geese_jobs_from_page.
        """
        job_ids = []
        try:
            job_rows = get_jobs_from_page(self.driver)
            for row in job_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 1:
                        continue
                    
                    job_title_elem = cells[0].find_element(By.TAG_NAME, "a")
                    href = job_title_elem.get_attribute("href")
                    
                    if href and "=" in href:
                        job_id = href.split("=")[-1]
                        job_ids.append(job_id)
                except Exception:
                    continue
        except Exception as e:
            print(f"      ✗ Error parsing job IDs: {e}")
        
        return job_ids
    
    def _get_jobs_from_folder(self, folder_name: str) -> List[str]:
        """
        Navigate to a folder and extract all job IDs (handles pagination).
        Returns list of job IDs.
        """
        try:
            print(f"   ⏳ Opening folder: '{folder_name}'...")
            
            if not navigate_to_folder(self.driver, folder_name):
                return []
            
            time.sleep(1)  # Let folder load
            
            # Get number of pages
            num_pages = get_pagination_pages(self.driver)
            print(f"      ℹ️  {num_pages} page(s) detected")
            
            all_job_ids = []
            
            for page in range(1, num_pages + 1):
                print(f"      ⏳ Scraping page {page}/{num_pages}...")
                
                job_ids = self._parse_job_ids_from_page()
                all_job_ids.extend(job_ids)
                print(f"         ✓ Found {len(job_ids)} jobs")
                
                if page < num_pages:
                    go_to_next_page(self.driver)
                    time.sleep(1)
            
            print(f"      ✓ Total: {len(all_job_ids)} jobs in '{folder_name}'")
            return all_job_ids
            
        except Exception as e:
            print(f"      ✗ Error getting jobs from folder '{folder_name}': {e}")
            return []
    
    def _ensure_job_in_supabase(self, job_id: str) -> bool:
        """
        Check if job exists in Supabase. If not, scrape and insert it.
        Returns True if job is now in Supabase, False otherwise.
        """
        if not self.use_supabase or not self.supabase:
            return True  # Skip if not using Supabase
        
        try:
            # Check if job exists
            existing_job = self.supabase.get_job_by_id(job_id)
            
            if existing_job:
                # Job already exists
                return True
            
            # Job doesn't exist - need to scrape it
            print(f"         ℹ️  Job {job_id} not in Supabase - scraping details...")
            
            if not self.scraper:
                print(f"         ⚠️  No scraper provided - cannot fetch job details")
                return False
            
            # Use scraper to get full job details
            # We need to navigate to the job and scrape it
            job_url = f"https://waterlooworks.uwaterloo.ca/myAccount/co-op/coop-postings.htm?ck_jobid={job_id}"
            self.driver.get(job_url)
            
            # Wait for job details to load
            if not smart_page_wait(
                self.driver,
                (By.CLASS_NAME, "is--long-form-reading"),
                max_wait=WaitTimes.MEDIUM
            ):
                print(f"         ✗ Job details page did not load for ID {job_id}")
                return False
            
            time.sleep(0.5)
            
            # Scrape the job details using the scraper's method
            job_data = self.scraper.scrape_single_job_details(job_id)
            
            if not job_data:
                print(f"         ✗ Could not scrape job {job_id}")
                return False
            
            # Insert into Supabase
            result = self.supabase.upsert_job(job_data)
            
            if result:
                print(f"         ✓ Added job {job_id} to Supabase")
                return True
            else:
                print(f"         ✗ Failed to insert job {job_id} into Supabase")
                return False
                
        except Exception as e:
            print(f"         ✗ Error ensuring job {job_id} in Supabase: {e}")
            return False
    
    def sync_all_folders(self) -> Dict[str, List[str]]:
        """
        Main sync function: scrapes all folders and their jobs.
        Returns the folders dictionary.
        """
        print("\n" + "="*60)
        print("🔄 STARTING FOLDER SYNC")
        print("="*60)
        
        # Get all folder cards
        folder_cards = self._get_all_folder_cards()
        
        if not folder_cards:
            print("\n   ✗ No folders found to sync")
            return {}
        
        print(f"\n   ✓ Found {len(folder_cards)} folder(s) to sync\n")
        
        folders_data = {}
        
        for idx, (folder_name, card) in enumerate(folder_cards, 1):
            print(f"\n📁 [{idx}/{len(folder_cards)}] Processing: '{folder_name}'")
            print("-" * 60)
            
            # Get all job IDs from this folder
            job_ids = self._get_jobs_from_folder(folder_name)
            
            if not job_ids:
                print(f"   ⚠️  No jobs found in '{folder_name}'")
                folders_data[folder_name] = []
                continue
            
            # Ensure all jobs are in Supabase
            if self.use_supabase:
                print(f"   ⏳ Syncing {len(job_ids)} jobs to Supabase...")
                
                synced_count = 0
                for job_id in job_ids:
                    if self._ensure_job_in_supabase(job_id):
                        synced_count += 1
                
                print(f"   ✓ {synced_count}/{len(job_ids)} jobs synced to Supabase")
            
            folders_data[folder_name] = job_ids
        
        # Save to file
        print("\n" + "="*60)
        print(f"💾 Saving folder data...")
        self._save_folders(folders_data)
        
        print("\n✅ FOLDER SYNC COMPLETE!")
        print("="*60)
        print(f"   • Total folders: {len(folders_data)}")
        print(f"   • Total jobs: {sum(len(jobs) for jobs in folders_data.values())}")
        print("="*60 + "\n")
        
        return folders_data
    
    def get_folders(self) -> Dict[str, List[str]]:
        """Get folders from local storage"""
        return self._load_folders()
