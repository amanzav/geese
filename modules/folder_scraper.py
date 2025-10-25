"""
Folder Scraper Module
Scrapes jobs from a specific WaterlooWorks folder and categorizes requirements using Gemini AI
"""

import time
import json
import re
import os
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import TIMEOUT, PAGE_LOAD


class FolderScraper:
    """Scrape and analyze jobs from a WaterlooWorks folder"""
    
    def __init__(self, driver, api_key=None):
        """
        Initialize folder scraper
        
        Args:
            driver: Selenium WebDriver instance
            api_key: Google Gemini API key for intelligent analysis
        """
        self.driver = driver
        
        # Configure Gemini for intelligent categorization
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        else:
            self.model = None
            print("⚠️  Warning: GEMINI_API_KEY not found. Falling back to pattern matching.")
    
    def navigate_to_folder(self, folder_name: str) -> bool:
        """
        Navigate to a specific WaterlooWorks folder
        
        Args:
            folder_name: Name of the folder (e.g., "geese", "good shit")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n📂 Navigating to folder: '{folder_name}'...")
            
            # Go to jobs page (same as apply.py)
            self.driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
            time.sleep(PAGE_LOAD)
            
            # Wait for stat cards to appear (same selector as apply.py)
            stat_cards = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".simple--stat-card.border-radius--16.display--flex.flex--column.dist--between")
                )
            )
            
            # Find the folder card by name
            folder_card = None
            for card in stat_cards:
                card_text = card.text.strip().lower()
                if folder_name.lower() in card_text:
                    folder_card = card
                    break
            
            if not folder_card:
                print(f"❌ Folder '{folder_name}' not found!")
                print("Available folders:")
                for card in stat_cards:
                    print(f"  - {card.text.strip()}")
                return False
            
            # Click the folder link (same as apply.py)
            link = folder_card.find_element(By.TAG_NAME, "a")
            link.click()
            time.sleep(PAGE_LOAD)
            
            print(f"✅ Navigated to '{folder_name}' folder")
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to folder: {e}")
            return False
    
    def get_job_rows(self):
        """Get all job rows from the current page (same as scraper.py)"""
        try:
            # Wait for table to load (same as scraper.py)
            table = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "data-viewer-table"))
            )
            time.sleep(1)
            
            # Get all job rows (skip header row [0])
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            return rows
        except Exception as e:
            print(f"❌ Error getting job rows: {e}")
            return []
    
    def parse_job_row(self, row):
        """
        Parse basic job info from a table row (same as scraper.py)
        
        Returns:
            dict with job_id, title, company, location, etc.
        """
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 8:
                return None
            
            # Get job ID from the row element (same as scraper.py)
            try:
                job_id = row.find_element(By.CLASS_NAME, "overflow--ellipsis").text.strip()
            except Exception:
                job_id = ""
            
            # Import utils helper for extracting cell text
            from .utils import get_cell_text, calculate_chances
            
            # Parse cells (same structure as scraper.py)
            job_data = {
                "id": job_id,
                "title": get_cell_text(cells[0]),
                "company": get_cell_text(cells[1]),
                "division": get_cell_text(cells[2]),
                "openings": get_cell_text(cells[3], "0"),
                "location": get_cell_text(cells[4]),
                "level": get_cell_text(cells[5]),
                "applications": get_cell_text(cells[6], "0"),
                "deadline": get_cell_text(cells[7]),
                "row_element": row,  # Store for clicking later
            }
            
            # Calculate chances ratio
            job_data["chances"] = calculate_chances(
                job_data["openings"], job_data["applications"]
            )
            
            return job_data
            
        except Exception as e:
            print(f"  ⚠️  Error parsing row: {e}")
            return None
    
    def get_job_details(self, job_data):
        """
        Click on a job and scrape detailed information (same as scraper.py)
        
        Args:
            job_data: Basic job data with row_element
        
        Returns:
            Enhanced job_data with detailed fields
        """
        try:
            row = job_data.get("row_element")
            if not row:
                return job_data

            # Find and click the job link (same as scraper.py)
            link = WebDriverWait(row, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, "a"))
            )

            # Scroll into view and adjust position to avoid click interception
            self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
            time.sleep(0.2)
            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(0.2)
            link.click()

            # Wait for job details panel to load (same as scraper.py)
            job_info = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "is--long-form-reading"))
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "js--question--container")
                )
            )
            time.sleep(2)

            # Extract description sections (same as scraper.py)
            job_divs = job_info.find_elements(By.CLASS_NAME, "js--question--container")

            sections = {
                "summary": "N/A",
                "responsibilities": "N/A",
                "skills": "N/A",
                "additional_info": "N/A",
                "employment_location_arrangement": "N/A",
                "work_term_duration": "N/A",
            }
            
            # Store compensation text separately (not in final output)
            compensation_raw = "N/A"

            for div in job_divs:
                text = div.get_attribute("innerText").strip()
                if text.startswith("Job Summary:"):
                    sections["summary"] = text.replace("Job Summary:", "", 1).strip()
                elif text.startswith("Job Responsibilities:"):
                    sections["responsibilities"] = text.replace(
                        "Job Responsibilities:", "", 1
                    ).strip()
                elif text.startswith("Required Skills:"):
                    sections["skills"] = text.replace("Required Skills:", "", 1).strip()
                elif text.startswith("Additional Application Information:"):
                    sections["additional_info"] = text.replace(
                        "Additional Application Information:", "", 1
                    ).strip()
                elif text.startswith("Employment Location Arrangement:"):
                    sections["employment_location_arrangement"] = text.replace(
                        "Employment Location Arrangement:", "", 1
                    ).strip()
                elif text.startswith("Work Term Duration:"):
                    sections["work_term_duration"] = text.replace(
                        "Work Term Duration:", "", 1
                    ).strip()
                elif text.startswith("Compensation and Benefits:"):
                    compensation_raw = text.replace(
                        "Compensation and Benefits:", "", 1
                    ).strip()

            # Parse compensation if available
            if compensation_raw != "N/A":
                sections["compensation"] = self._parse_compensation(compensation_raw)
            else:
                sections["compensation"] = {
                    "value": None,
                    "currency": None,
                    "original_text": "N/A",
                    "time_period": None
                }

            # Add description fields to job data
            job_data.update(sections)

            # Close the details panel (same as scraper.py)
            self.close_job_details_panel()

            # Remove row_element (can't be serialized to JSON)
            del job_data["row_element"]
            return job_data

        except Exception as e:
            print(f"  ⚠️  Error getting job details for {job_data.get('id', 'unknown')}: {e}")
            if "row_element" in job_data:
                del job_data["row_element"]
            return job_data
    
    def close_job_details_panel(self):
        """Close the currently open job details panel (same as scraper.py)"""
        try:
            close_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "[class='btn__default--text btn--default protip']"
            )
            if close_buttons:
                close_buttons[-1].click()
                time.sleep(1)
                return True
            return False
        except Exception as e:
            print(f"  ⚠️  Error closing job panel: {e}")
            return False
    
    def _parse_compensation(self, comp_text):
        """Parse compensation text into structured format"""
        # Try to extract hourly/salary info
        hourly_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)\s*[-–]\s*\$?([\d,]+(?:\.\d{2})?)\s*/\s*h', comp_text, re.IGNORECASE)
        if hourly_match:
            low = float(hourly_match.group(1).replace(',', ''))
            high = float(hourly_match.group(2).replace(',', ''))
            return {
                "value": high,
                "range": {"min": low, "max": high},
                "currency": "CAD",
                "time_period": "hourly",
                "original_text": comp_text
            }
        
        # Try single hourly rate
        single_hourly = re.search(r'\$?([\d,]+(?:\.\d{2})?)\s*/\s*h', comp_text, re.IGNORECASE)
        if single_hourly:
            value = float(single_hourly.group(1).replace(',', ''))
            return {
                "value": value,
                "currency": "CAD",
                "time_period": "hourly",
                "original_text": comp_text
            }
        
        # Return original text if can't parse
        return {
            "value": None,
            "currency": "CAD",
            "time_period": "unknown",
            "original_text": comp_text
        }
    
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
    
    def get_pagination_pages(self):
        """Get the number of pages in the current view (same as scraper.py)"""
        try:
            pagination = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
            )
            page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
            return page_buttons
        except Exception:
            return 1
    
    def next_page(self):
        """Go to the next page in pagination (same as scraper.py)"""
        try:
            pagination = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
            )
            next_button = pagination.find_elements(By.TAG_NAME, "li")[-2]
            next_button.find_element(By.TAG_NAME, "a").click()
            time.sleep(PAGE_LOAD)
        except Exception as e:
            print(f"  ⚠️  Error navigating to next page: {e}")
    
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
        
        # Get all job rows
        rows = self.get_job_rows()
        total_jobs = len(rows)
        
        if total_jobs == 0:
            return []
        
        # Process each job
        for i, row in enumerate(rows, 1):
            try:
                # Parse basic info
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
                
                # Get detailed information
                print(f"           🔍 Scraping details...", end=" ")
                job_data = self.get_job_details(job_data)
                print("✓")
                
                # Analyze requirements with Gemini
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
        
        # Navigate to folder
        if not self.navigate_to_folder(folder_name):
            return []
        
        print("\n" + "=" * 70)
        print("🔄 SCRAPING AND ANALYZING JOBS")
        print("=" * 70)
        print()
        
        # Check for pagination
        try:
            num_pages = self.get_pagination_pages()
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
            
            # Go to next page if not the last one
            if page < num_pages:
                print(f"\n➡️  Going to page {page + 1}...\n")
                self.next_page()
                time.sleep(PAGE_LOAD)
        
        print("=" * 70)
        print(f"✅ Successfully scraped {len(all_jobs)} jobs")
        print("=" * 70)
        
        return all_jobs
