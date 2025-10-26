"""Folder Scraper Module - Extends scraper with AI requirements analysis"""

import time
import json
import re
import os
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import TIMEOUT, PAGE_LOAD, navigate_to_folder, get_pagination_pages, go_to_next_page
from .scraper import WaterlooWorksScraper


class FolderScraper(WaterlooWorksScraper):
    """Scrape and analyze jobs from a WaterlooWorks folder with AI-powered requirements analysis"""
    
    def __init__(self, driver, api_key=None):
        """Initialize folder scraper
        
        Args:
            driver: Selenium WebDriver instance
            api_key: Google Gemini API key for intelligent analysis
        """
        super().__init__(driver)
        
        # Configure Gemini for intelligent categorization
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        else:
            self.model = None
            print("⚠️  Warning: GEMINI_API_KEY not found. Falling back to pattern matching.")
    
    def navigate_to_folder(self, folder_name: str) -> bool:
        """Navigate to a specific WaterlooWorks folder"""
        print(f"\n📂 Navigating to folder: '{folder_name}'...")
        success = navigate_to_folder(self.driver, folder_name)
        if success:
            print(f"✅ Navigated to '{folder_name}' folder")
        return success
    
    def analyze_requirements(self, job_data):
        """
        Use Gemini AI to analyze job requirements and categorize them
        
        Args:
            job_data: Job data with additional_info field
        
        Returns:
            dict with categorized requirements
        """
        additional_info = job_data.get("additional_info", "N/A")
        
        # If no additional info, return standard
        if not additional_info or additional_info == "N/A" or len(additional_info) < 20:
            return {
                "external_application": {
                    "required": False,
                    "url": None
                },
                "extra_documents": {
                    "required": False,
                    "documents": []
                },
                "bonus_items": {
                    "available": False,
                    "items": []
                }
            }
        
        # Use Gemini if available
        if self.model:
            try:
                prompt = f"""Analyze this job posting's additional information and extract requirement details.

Job: {job_data.get('title')} at {job_data.get('company')}
Additional Info: {additional_info}

Extract the following as JSON:

1. External Application:
   - Does it require applying through an external website (not just WaterlooWorks)?
   - If yes, what's the URL?

2. Extra Documents (REQUIRED documents beyond resume/cover letter):
   - Transcripts
   - Portfolios
   - Reference letters
   - Work samples
   - Any other mandatory documents

3. Bonus Items (OPTIONAL things that make you stand out):
   - Optional portfolios
   - Project demos
   - GitHub contributions
   - Video presentations
   - Any optional materials mentioned

Format as JSON:
{{
  "external_application": {{
    "required": true/false,
    "url": "https://..." or null
  }},
  "extra_documents": {{
    "required": true/false,
    "documents": ["transcript", "portfolio", ...]
  }},
  "bonus_items": {{
    "available": true/false,
    "items": ["project demo video", "github contributions", ...]
  }}
}}"""

                response = self.model.generate_content(prompt)
                text = response.text.strip()
                
                # Extract JSON
                if "```json" in text:
                    json_str = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    json_str = text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = text
                
                result = json.loads(json_str)
                return result
                
            except Exception as e:
                print(f"  ⚠️  Gemini analysis failed: {e}")
                # Fall back to pattern matching
        
        # Pattern matching fallback
        return self._pattern_match_requirements(additional_info)
    
    def _pattern_match_requirements(self, additional_info):
        """Fallback pattern matching for requirement analysis"""
        lower_info = additional_info.lower()
        
        # Check for external application
        external_required = False
        external_url = None
        
        if re.search(r'apply.*(?:through|via|at|to).*https?://', lower_info, re.IGNORECASE):
            external_required = True
            urls = re.findall(r'https?://\S+', additional_info)
            if urls:
                external_url = urls[0]
        
        # Check for extra documents (required)
        extra_docs_required = False
        documents = []
        
        required_doc_patterns = [
            (r'\btranscript', 'transcript'),
            (r'\bportfolio\b(?!.*optional)', 'portfolio'),
            (r'\breference\s+letter', 'reference letter'),
            (r'\bwork\s+sample', 'work sample'),
            (r'\bwriting\s+sample', 'writing sample'),
            (r'\bproof\s+of', 'proof of citizenship/status'),
            (r'\bpolice\s+check', 'police check'),
        ]
        
        for pattern, doc_name in required_doc_patterns:
            if re.search(pattern, lower_info) and 'optional' not in lower_info[max(0, lower_info.find(doc_name.lower())-50):lower_info.find(doc_name.lower())+50]:
                extra_docs_required = True
                documents.append(doc_name)
        
        # Check for bonus items (optional)
        bonus_available = False
        bonus_items = []
        
        bonus_keywords = [
            'optional', 'bonus', 'stand out', 'set you apart', 
            'preferred', 'nice to have', 'showcase', 'impress'
        ]
        
        if any(keyword in lower_info for keyword in bonus_keywords):
            bonus_available = True
            
            # Try to extract what the bonus items are
            if 'portfolio' in lower_info and 'optional' in lower_info:
                bonus_items.append('optional portfolio')
            if 'project' in lower_info and ('demo' in lower_info or 'showcase' in lower_info):
                bonus_items.append('project demo')
            if 'github' in lower_info or 'git' in lower_info:
                bonus_items.append('github contributions')
            if 'video' in lower_info:
                bonus_items.append('video presentation')
        
        return {
            "external_application": {
                "required": external_required,
                "url": external_url
            },
            "extra_documents": {
                "required": extra_docs_required,
                "documents": documents
            },
            "bonus_items": {
                "available": bonus_available,
                "items": bonus_items
            }
        }
    
    def scrape_page_with_analysis(self, existing_jobs=None):
        """
        Scrape all jobs from current page and analyze their requirements
        
        Args:
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
        
        Returns:
            List of jobs with detailed info and categorized requirements
        """
        if existing_jobs is None:
            existing_jobs = {}
        
        jobs = []
        new_jobs_count = 0
        
        # Get all job rows from parent's get_job_table method
        rows = self.get_job_table()
        total_jobs = len(rows)
        
        if total_jobs == 0:
            return []
        
        # Process each job
        for i, row in enumerate(rows, 1):
            try:
                # Parse basic info using parent's method
                job_data = self.parse_job_row(row)
                if not job_data or not job_data.get('id'):
                    continue
                
                job_id = job_data.get('id')
                
                # Check if job already exists in cache
                if job_id in existing_jobs:
                    print(f"[{i}/{total_jobs}] ⏭️  Skipping: {job_data.get('title', 'Unknown')} (already cached)")
                    # Use cached version (already has details and requirements)
                    jobs.append(existing_jobs[job_id])
                    continue
                
                print(f"[{i}/{total_jobs}] {job_data.get('title', 'Unknown')} @ {job_data.get('company', 'N/A')}")
                
                # Get detailed information using parent's method
                print(f"           🔍 Scraping details...", end=" ")
                job_data = self.get_job_details(job_data)
                print("✓")
                
                # Analyze requirements with Gemini (unique to FolderScraper)
                print(f"           🧠 Analyzing requirements...", end=" ")
                requirements = self.analyze_requirements(job_data)
                job_data["requirements"] = requirements
                print("✓")
                
                # Show categorization
                if requirements["external_application"]["required"]:
                    print(f"           🔗 External application required")
                if requirements["extra_documents"]["required"]:
                    print(f"           📎 Extra documents: {', '.join(requirements['extra_documents']['documents'])}")
                if requirements["bonus_items"]["available"]:
                    print(f"           ⭐ Bonus items available")
                
                jobs.append(job_data)
                new_jobs_count += 1
                print()
                
            except Exception as e:
                print(f"  ❌ Error processing job: {e}")
                continue
        
        return jobs
    
    def scrape_folder_with_analysis(self, folder_name: str, existing_jobs=None):
        """
        Scrape all jobs from a folder (all pages) and analyze their requirements
        
        Args:
            folder_name: Name of the WaterlooWorks folder
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
        
        Returns:
            List of jobs with detailed info and categorized requirements
        """
        if existing_jobs is None:
            existing_jobs = {}
        
        # Navigate to folder using utils function
        if not self.navigate_to_folder(folder_name):
            return []
        
        print("\n" + "=" * 70)
        print("🔄 SCRAPING AND ANALYZING JOBS")
        print("=" * 70)
        print()
        
        # Check for pagination using utils function
        try:
            num_pages = get_pagination_pages(self.driver)
            print(f"📄 Total pages: {num_pages}\n")
        except Exception:
            print("📄 Single page (no pagination)\n")
            num_pages = 1
        
        all_jobs = []
        
        # Scrape all pages
        for page in range(1, num_pages + 1):
            print(f"📄 Scraping page {page}/{num_pages}...")
            print()
            
            page_jobs = self.scrape_page_with_analysis(existing_jobs=existing_jobs)
            all_jobs.extend(page_jobs)
            
            # Go to next page if not the last one using utils function
            if page < num_pages:
                print(f"\n➡️  Going to page {page + 1}...\n")
                go_to_next_page(self.driver)
                time.sleep(PAGE_LOAD)
        
        print("=" * 70)
        print(f"✅ Successfully scraped {len(all_jobs)} jobs")
        print("=" * 70)
        
        return all_jobs
