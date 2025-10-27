"""Scraper Module - Handles job scraping and navigation on WaterlooWorks"""

import time
import traceback
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import (
    TIMEOUT, PAGE_LOAD, SELECTORS, WaitTimes,
    get_cell_text, calculate_chances,
    get_pagination_pages, go_to_next_page,
    close_job_details_panel,
    smart_page_wait, click_and_wait, smart_element_click, fast_presence_check,
    timer
)
from .agents import AgentFactory
from .database import get_db


class WaterlooWorksScraper:
    """Handle job scraping on WaterlooWorks"""

    def __init__(self, driver, llm_provider="gemini"):
        """Initialize scraper
        
        Args:
            driver: Selenium WebDriver instance (from auth)
            llm_provider: LLM provider for compensation extraction (deprecated - uses config)
        """
        self.driver = driver
        self.llm_provider = llm_provider  # Kept for backwards compatibility
        self._agent_factory = None
        self._keyword_agent = None

    def go_to_jobs_page(self):
        """Navigate to jobs page and apply optional program filter - OPTIMIZED"""
        print("📋 Navigating to jobs page...")

        self.driver.get(
            "https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm"
        )
        
        # Smart wait for page load
        smart_page_wait(self.driver, (By.CSS_SELECTOR, ".doc-viewer--filter-bar button"))

        print("🔘 Clicking initial filter button...")
        filter_button = fast_presence_check(
            self.driver, 
            ".doc-viewer--filter-bar button"
        )
        if filter_button:
            click_and_wait(
                self.driver, 
                filter_button,
                wait_for=(By.CSS_SELECTOR, ".btn__default.btn--black.tag-rail__menu-btn"),
                max_wait=WaitTimes.MEDIUM
            )
        else:
            print("   ⚠️  Filter button not found")
            return

        # Apply program filter
        print(f"🎯 Applying program filter...")

        filter_menu_button = fast_presence_check(
            self.driver,
            ".btn__default.btn--black.tag-rail__menu-btn"
        )
        if filter_menu_button:
            click_and_wait(
                self.driver,
                filter_menu_button,
                wait_for=(By.CSS_SELECTOR, ".color--bg--white.doc-viewer input"),
                max_wait=WaitTimes.MEDIUM
            )

        # Find and click the program checkbox
        program_checkbox = fast_presence_check(
            self.driver,
            ".color--bg--white.doc-viewer input"
        )
        if program_checkbox:
            smart_element_click(self.driver, program_checkbox, scroll_first=False)

        # Close the sidebar
        print("🔘 Closing filter sidebar...")
        filter_button_close = fast_presence_check(
            self.driver,
            ".btn__default.btn--black.tag-rail__menu-btn"
        )
        if filter_button_close:
            click_and_wait(self.driver, filter_button_close, max_wait=WaitTimes.FAST)

        print("✅ Program filter applied\n")

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
                job_id = row.find_element(
                    By.CLASS_NAME, "overflow--ellipsis"
                ).text.strip()
            except Exception as e:
                print(f"  ⚠️  Warning: Could not extract job ID: {e}")
                job_id = ""

            # Extract job data from cells
            job_data = {
                "id": job_id,
                "title": get_cell_text(cells[0]),
                "company": get_cell_text(cells[1]),
                "division": get_cell_text(cells[2]),
                "openings": get_cell_text(cells[3], "0"),
                "location": get_cell_text(cells[4]),  # Use 'location' instead of 'city'
                "level": get_cell_text(cells[5]),
                "applications": get_cell_text(cells[6], "0"),
                "deadline": get_cell_text(cells[7]),
                "row_element": row,  # Keep reference for clicking later
            }

            # Calculate chances ratio
            job_data["chances"] = calculate_chances(
                job_data["openings"], job_data["applications"]
            )

            return job_data
        except Exception as e:
            print(f"⚠️  Error parsing job row: {e}")
            traceback.print_exc()
            return None

    def get_job_details(self, job_data):
        """Click into a job and extract full description details - OPTIMIZED"""
        try:
            row = job_data.get("row_element")
            if not row:
                return job_data

            # Find and click the job link with optimized scrolling
            link = fast_presence_check(row, "a", by=By.TAG_NAME, timeout=WaitTimes.MEDIUM)
            if not link:
                print("   ⚠️  Job link not found")
                return job_data
            
            # Smart click with single scroll
            smart_element_click(self.driver, link)

            # Fast wait for job details panel (poll every 50ms)
            job_info = WebDriverWait(self.driver, WaitTimes.SLOW, poll_frequency=0.05).until(
                EC.presence_of_element_located((By.CLASS_NAME, "is--long-form-reading"))
            )
            
            # Fast wait for question containers (poll every 50ms)
            WebDriverWait(self.driver, WaitTimes.SLOW, poll_frequency=0.05).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "js--question--container")
                )
            )
            
            # Minimal wait for dynamic content
            time.sleep(WaitTimes.FAST)

            # Extract description sections
            job_divs = job_info.find_elements(By.CLASS_NAME, "js--question--container")

            # Section mapping for cleaner extraction
            SECTION_MAPPINGS = {
                "Job Summary:": "summary",
                "Job Responsibilities:": "responsibilities",
                "Required Skills:": "skills",
                "Additional Application Information:": "additional_info",
                "Employment Location Arrangement:": "employment_location_arrangement",
                "Work Term Duration:": "work_term_duration",
                "Compensation and Benefits:": "_compensation_raw",  # Special handling below
            }

            sections = {key: "N/A" for key in SECTION_MAPPINGS.values() if not key.startswith("_")}
            compensation_raw = "N/A"

            for div in job_divs:
                text = div.get_attribute("innerText").strip()
                
                # Check each section mapping
                for prefix, section_key in SECTION_MAPPINGS.items():
                    if text.startswith(prefix):
                        content = text.replace(prefix, "", 1).strip()
                        if section_key == "_compensation_raw":
                            compensation_raw = content
                        else:
                            sections[section_key] = content
                        break  # Found matching section, move to next div

            # Extract compensation using LLM agent
            if compensation_raw != "N/A":
                try:
                    # Lazy initialize keyword agent for compensation extraction
                    if self._keyword_agent is None:
                        if self._agent_factory is None:
                            from .config import load_app_config
                            config = load_app_config()
                            agent_config = {
                                "keyword_extractor_agent": {
                                    "provider": config.agents.keyword_extractor_agent.get("provider", "groq"),
                                    "model": config.agents.keyword_extractor_agent.get("model", "llama-3.1-8b-instant")
                                }
                            }
                            self._agent_factory = AgentFactory(
                                config=agent_config,
                                enable_tracking=config.agents.enable_token_tracking
                            )
                        self._keyword_agent = self._agent_factory.get_keyword_extractor_agent()
                    
                    comp_data = self._keyword_agent.extract_compensation(compensation_raw)
                    sections["compensation"] = comp_data
                except Exception as e:
                    print(f"  ⚠️  Error extracting compensation: {e}")
                    traceback.print_exc()
                    sections["compensation"] = {
                        "value": None,
                        "currency": None,
                        "original_text": compensation_raw,
                        "time_period": None
                    }
            else:
                sections["compensation"] = {
                    "value": None,
                    "currency": None,
                    "original_text": "N/A",
                    "time_period": None
                }

            # Add description fields to job data
            job_data.update(sections)
            # Note: No longer creating combined 'description' field to avoid duplication

            # DON'T close the panel here - let the caller decide when to close
            # This allows save_job_to_folder to work with the open panel

            # Remove row_element (can't be serialized to JSON)
            del job_data["row_element"]
            return job_data

        except Exception as e:
            print(f"❌ Error getting job details for {job_data.get('id', 'unknown')}: {e}")
            traceback.print_exc()
            if "row_element" in job_data:
                del job_data["row_element"]
            return job_data

    def save_job_to_folder(self, job_data, folder_name: Optional[str] = None):
        """
        Save a job to a specific folder in WaterlooWorks

        Args:
            job_data: Job data dictionary (must have 'row_element' or be in details view)
            folder_name: Name of the folder to save to (uses config if not specified)

        Returns:
            bool: True if successful, False otherwise
        """
        if folder_name is None:
            from .config import load_app_config
            config = load_app_config()
            folder_name = config.get("waterlooworks_folder", "geese")
        try:
            # Check if panel is already open, if not, open it
            panel_already_open = False
            try:
                # Check if job details panel is present
                self.driver.find_element(By.CLASS_NAME, "is--long-form-reading")
                panel_already_open = True
            except:
                panel_already_open = False
            
            # If panel not open and we have a row element, click it to open details
            if not panel_already_open and "row_element" in job_data:
                row = job_data["row_element"]
                link = WebDriverWait(row, 10).until(
                    EC.visibility_of_element_located((By.TAG_NAME, "a"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(0.2)
                self.driver.execute_script("window.scrollBy(0, -100);")
                time.sleep(0.2)
                link.click()

                # Wait for job details to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "is--long-form-reading")
                    )
                )
                time.sleep(1)

            # Step 1: Click the "Add to folder" button (2nd button in floating action bar)
            print(
                f"  📁 Opening folder selection for: {job_data.get('title', 'Unknown')}"
            )
            add_to_folder_buttons = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".floating--action-bar.color--bg--default button")
                )
            )

            if len(add_to_folder_buttons) < 2:
                print(f"  ❌ Could not find 'Add to folder' button")
                return False

            # Click the second button (index 1)
            self.driver.execute_script(
                "arguments[0].click();", add_to_folder_buttons[1]
            )
            time.sleep(1)

            # Step 2: Find the folder with the specified name
            print(f"  🔍 Looking for folder: {folder_name}")
            folder_labels = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        ".toggle--single.margin--a--none.padding--a--none",
                    )
                )
            )

            folder_found = False
            for label in folder_labels:
                try:
                    # Check if this label contains a <p> tag with the folder name
                    p_tags = label.find_elements(By.TAG_NAME, "p")
                    for p_tag in p_tags:
                        if p_tag.text.strip().lower() == folder_name.lower():
                            # Found the right folder! Now click its checkbox
                            print(f"  ✅ Found folder: {folder_name}")
                            checkbox = label.find_element(
                                By.CSS_SELECTOR, 'input[type="checkbox"]'
                            )
                            self.driver.execute_script(
                                "arguments[0].click();", checkbox
                            )
                            time.sleep(0.5)
                            folder_found = True
                            break
                except Exception as e:
                    continue

                if folder_found:
                    break

            if not folder_found:
                print(f"  ⚠️  Folder '{folder_name}' not found. Available folders:")
                for label in folder_labels:
                    try:
                        p_tags = label.find_elements(By.TAG_NAME, "p")
                        for p_tag in p_tags:
                            if p_tag.text.strip():
                                print(f"     - {p_tag.text.strip()}")
                    except Exception:
                        pass
                return False

            # Step 3: Click the Save button
            print(f"  💾 Saving to folder...")
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        ".btn__hero--text.btn--default.margin--r--s.width--100",
                    )
                )
            )
            self.driver.execute_script("arguments[0].click();", save_button)
            time.sleep(1)

            print(f"  ✅ Successfully saved job to '{folder_name}' folder")
            
            # Close the job details panel after saving
            close_job_details_panel(self.driver)
            
            return True

        except Exception as e:
            print(f"  ❌ Error saving job to folder: {e}")
            return False
    
    def scrape_current_page(
        self,
        include_details=False,
        existing_jobs=None,
        all_jobs=None,
        save_every=5,
    ):
        """Scrape all jobs from the current page, skipping already-scraped jobs

        Args:
            include_details: Whether to deep scrape job details
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
            all_jobs: Accumulated list of all jobs (for incremental saves)
            save_every: Save after this many new jobs scraped (default: 5)
        """
        if existing_jobs is None:
            existing_jobs = {}
        if all_jobs is None:
            all_jobs = []

        jobs = []
        rows = self.get_job_table()
        new_jobs_count = 0

        for i, row in enumerate(rows, 1):
            job_data = self.parse_job_row(row)
            if job_data and job_data.get("id"):
                job_id = job_data.get("id")

                # Check if job already exists in cache
                if job_id in existing_jobs:
                    print(
                        f"  ⏭️  Skipping job {i}/{len(rows)}: {job_data.get('title', 'Unknown')} (already cached)"
                    )
                    # Use cached version (already has details)
                    jobs.append(existing_jobs[job_id])
                else:
                    # New job - scrape details if requested
                    if include_details:
                        print(
                            f"  → Getting details for job {i}/{len(rows)}: {job_data.get('title', 'Unknown')}"
                        )
                        job_data = self.get_job_details(job_data)
                        # Fast panel close - no waiting for animation
                        close_buttons = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS["close_panel_button"])
                        if close_buttons:
                            smart_element_click(self.driver, close_buttons[-1], scroll_first=False)
                    else:
                        # Remove row_element if not getting details
                        if "row_element" in job_data:
                            del job_data["row_element"]
                    jobs.append(job_data)
                    new_jobs_count += 1

                    # Incremental save after every N new jobs
                    if save_every > 0 and new_jobs_count % save_every == 0:
                        # Save to database
                        from modules.database import get_db
                        db = get_db()
                        saved = self.save_jobs_to_database(jobs[-save_every:])
                        print(
                            f"  💾 Auto-saved {saved} jobs ({len(all_jobs) + len(jobs)} total)..."
                        )

        print(f"✅ Parsed {len(jobs)} jobs from this page ({new_jobs_count} new)\n")
        return jobs

    def scrape_all_jobs(
        self,
        include_details=False,
        existing_jobs=None,
        save_every=5,
        use_database=True,
    ):
        """Scrape all jobs from all pages with incremental saving to database

        Args:
            include_details: Whether to deep scrape job details
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
            save_every: Save after this many new jobs scraped (default: 5)
            use_database: Whether to save to database (default: True)
        """
        if existing_jobs is None:
            # Load from database if not provided
            if use_database:
                db = get_db()
                existing_jobs = db.get_jobs_dict()
            else:
                existing_jobs = {}

        print("🔍 Starting full job scrape...\n")
        
        with timer("Full scrape"):
            all_jobs = []

            # Check for pagination
            try:
                num_pages = get_pagination_pages(self.driver)
                print(f"📄 Total pages: {num_pages}\n")
            except Exception:
                print("📄 Single page (no pagination)\n")
                num_pages = 1

            # Scrape all pages
            for page in range(1, num_pages + 1):
                with timer(f"Page {page}/{num_pages}"):
                    print(f"📄 Scraping page {page}/{num_pages}...")
                    jobs = self.scrape_current_page(
                        include_details=include_details,
                        existing_jobs=existing_jobs,
                        all_jobs=all_jobs,
                        save_every=save_every,
                    )
                    all_jobs.extend(jobs)

                    # Save to database after each page
                    if use_database and jobs:
                        saved = self.save_jobs_to_database(jobs)
                        print(f"💾 Saved {saved} jobs to database\n")

                # Go to next page if not the last one
                if page < num_pages:
                    print(f"➡️  Going to page {page + 1}...\n")
                    go_to_next_page(self.driver)

            print(f"\n🎉 Total jobs scraped: {len(all_jobs)}")
            
            if use_database:
                print(f"✅ All jobs saved to database\n")
            
            return all_jobs

    def save_jobs_to_database(self, jobs):
        """Save scraped jobs to SQLite database
        
        Args:
            jobs: List of job dictionaries to save
            
        Returns:
            int: Number of jobs successfully saved
        """
        db = get_db()
        saved_count = 0
        
        for job in jobs:
            if db.insert_job(job):
                saved_count += 1
        
        return saved_count
