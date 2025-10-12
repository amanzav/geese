"""
Scraper Module for Geese
Handles job scraping and navigation on WaterlooWorks
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import TIMEOUT, PAGE_LOAD, get_cell_text, calculate_chances


class WaterlooWorksScraper:
    """Handle job scraping on WaterlooWorks"""
    
    def __init__(self, driver):
        """
        Initialize scraper with an existing browser driver
        
        Args:
            driver: Selenium WebDriver instance (from auth)
        """
        self.driver = driver
    
    def go_to_jobs_page(self, program_filter_value=None):
        """Navigate to jobs page and apply optional program filter"""
        print("📋 Navigating to jobs page...")
        
        self.driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        time.sleep(PAGE_LOAD)
        
        print("🔘 Clicking initial filter button...")
        filter_button = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.doc-viewer--filter-bar button'))
        )
        filter_button.click()
        time.sleep(PAGE_LOAD)
        
        # Apply program filter if provided
        if program_filter_value:
            print(f"🎯 Applying program filter ({program_filter_value})...")
            
            filter_menu_button = WebDriverWait(self.driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn__default.btn--black.tag-rail__menu-btn'))
            )
            filter_menu_button.click()
            time.sleep(PAGE_LOAD)
            
            # Find and click the program checkbox
            program_checkbox = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f'.color--bg--white.doc-viewer input[value="{program_filter_value}"]')
                )
            )
            self.driver.execute_script("arguments[0].click();", program_checkbox)
            time.sleep(PAGE_LOAD)
            
            # Close the sidebar
            close_button = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.js--btn--close-sidebar'))
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            time.sleep(PAGE_LOAD)
            
            print("✅ Program filter applied\n")
        else:
            print("✅ Jobs page loaded (no filter applied)\n")
    
    def get_job_table(self):
        """Get all rows from the current job listings table"""
        print("📊 Getting job listings...")
        
        table = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "data-viewer-table"))
        )
        
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
        print(f"✅ Found {len(rows)} jobs on this page\n")
        return rows
    
    def parse_job_row(self, row):
        """Extract job information from a table row"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                return None
            
            # Get job ID from the row element
            try:
                job_id = row.find_element(By.CLASS_NAME, "overflow--ellipsis").text.strip()
            except Exception:
                job_id = ""
            
            # Extract job data from cells
            job_data = {
                "id": job_id,
                "title": get_cell_text(cells[0]),
                "company": get_cell_text(cells[1]),
                "division": get_cell_text(cells[2]),
                "openings": get_cell_text(cells[3], "0"),
                "city": get_cell_text(cells[4]),
                "level": get_cell_text(cells[5]),
                "applications": get_cell_text(cells[6], "0"),
                "deadline": get_cell_text(cells[7]),
                "row_element": row,  # Keep reference for clicking later
            }
            
            # Calculate chances ratio
            job_data["chances"] = calculate_chances(
                job_data["openings"], 
                job_data["applications"]
            )
            
            return job_data
        except Exception as e:
            print(f"Error parsing row: {e}")
            return None
    
    def get_job_details(self, job_data):
        """Click into a job and extract full description details"""
        try:
            row = job_data.get("row_element")
            if not row:
                return job_data
            
            # Find and click the job link
            link = WebDriverWait(row, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Scroll into view and adjust position to avoid click interception
            self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
            time.sleep(0.2)
            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(0.2)
            link.click()
            
            # Wait for job details panel to load
            job_info = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "is--long-form-reading"))
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js--question--container"))
            )
            time.sleep(2)
            
            # Extract description sections
            job_divs = job_info.find_elements(By.CLASS_NAME, "js--question--container")
            
            sections = {
                "summary": "N/A",
                "responsibilities": "N/A",
                "skills": "N/A",
                "additional_info": "N/A"
            }
            
            for div in job_divs:
                text = div.get_attribute("innerText").strip()
                if text.startswith("Job Summary:"):
                    sections["summary"] = text
                elif text.startswith("Job Responsibilities:"):
                    sections["responsibilities"] = text
                elif text.startswith("Required Skills:"):
                    sections["skills"] = text
                elif text.startswith("Additional Application Information:"):
                    sections["additional_info"] = text
            
            # Add description fields to job data
            job_data.update(sections)
            job_data["description"] = f"{sections['summary']}\n\n{sections['responsibilities']}\n\n{sections['skills']}"
            
            # Close the job details panel
            close_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "[class='btn__default--text btn--default protip']"
            )
            if close_buttons:
                close_buttons[-1].click()
                time.sleep(1)
            
            # Remove row_element (can't be serialized to JSON)
            del job_data["row_element"]
            return job_data
            
        except Exception as e:
            print(f"Error getting job details for {job_data.get('id', 'unknown')}: {e}")
            if "row_element" in job_data:
                del job_data["row_element"]
            return job_data
    
    def scrape_current_page(self, include_details=False):
        """Scrape all jobs from the current page"""
        jobs = []
        rows = self.get_job_table()
        
        for i, row in enumerate(rows, 1):
            job_data = self.parse_job_row(row)
            if job_data and job_data.get('id'):
                if include_details:
                    print(f"  → Getting details for job {i}/{len(rows)}: {job_data.get('title', 'Unknown')}")
                    job_data = self.get_job_details(job_data)
                else:
                    # Remove row_element if not getting details
                    if "row_element" in job_data:
                        del job_data["row_element"]
                jobs.append(job_data)
        
        print(f"✅ Parsed {len(jobs)} jobs from this page\n")
        return jobs
    
    def scrape_all_jobs(self, include_details=False):
        """Scrape all jobs from all pages"""
        print("🔍 Starting full job scrape...\n")
        all_jobs = []
        
        # Check for pagination
        try:
            num_pages = self.get_pagination_pages()
            print(f"📄 Total pages: {num_pages}\n")
        except Exception:
            print("📄 Single page (no pagination)\n")
            num_pages = 1
        
        # Scrape all pages
        for page in range(1, num_pages + 1):
            print(f"📄 Scraping page {page}/{num_pages}...")
            jobs = self.scrape_current_page(include_details=include_details)
            all_jobs.extend(jobs)
            
            # Go to next page if not the last one
            if page < num_pages:
                print(f"➡️  Going to page {page + 1}...\n")
                self.next_page()
        
        print(f"\n🎉 Total jobs scraped: {len(all_jobs)}")
        return all_jobs
    
    def get_pagination_pages(self):
        """Get the number of pages in the current view"""
        pagination = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
        return page_buttons
    
    def next_page(self):
        """Go to the next page in pagination"""
        pagination = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        next_button = pagination.find_elements(By.TAG_NAME, "li")[-2]
        next_button.find_element(By.TAG_NAME, "a").click()
        time.sleep(PAGE_LOAD)
