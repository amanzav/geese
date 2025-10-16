"""
Scraper Module for Geese
Handles job scraping and navigation on WaterlooWorks
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils import TIMEOUT, PAGE_LOAD, get_cell_text, calculate_chances
from .llm_assistant import CompensationExtractor


class WaterlooWorksScraper:
    """Handle job scraping on WaterlooWorks"""

    def __init__(self, driver, llm_provider="gemini"):
        """
        Initialize scraper with an existing browser driver

        Args:
            driver: Selenium WebDriver instance (from auth)
            llm_provider: LLM provider for compensation extraction ("gemini" or "openai")
        """
        self.driver = driver
        self.llm_provider = llm_provider
        self.compensation_extractor = None  # Lazy initialization

    def go_to_jobs_page(self):
        """Navigate to jobs page and apply optional program filter"""
        print("📋 Navigating to jobs page...")

        self.driver.get(
            "https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm"
        )
        time.sleep(PAGE_LOAD)

        print("🔘 Clicking initial filter button...")
        filter_button = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".doc-viewer--filter-bar button")
            )
        )
        filter_button.click()
        time.sleep(PAGE_LOAD)

        # Apply program filter if provided
        print(f"🎯 Applying program filter...")

        filter_menu_button = WebDriverWait(self.driver, TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".btn__default.btn--black.tag-rail__menu-btn")
            )
        )
        filter_menu_button.click()
        time.sleep(PAGE_LOAD)

        # Find and click the program checkbox
        program_checkbox = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".color--bg--white.doc-viewer input")
            )
        )
        self.driver.execute_script("arguments[0].click();", program_checkbox)
        time.sleep(PAGE_LOAD)

        # Close the sidebar by re-finding and clicking the filter button again
        print("🔘 Closing filter sidebar...")
        filter_button_close = WebDriverWait(self.driver, TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".btn__default.btn--black.tag-rail__menu-btn")
            )
        )
        filter_button_close.click()
        time.sleep(PAGE_LOAD)

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
            except Exception:
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
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "js--question--container")
                )
            )
            time.sleep(2)

            # Extract description sections
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

            # Extract compensation using LLM
            if compensation_raw != "N/A":
                try:
                    # Lazy initialize compensation extractor
                    if self.compensation_extractor is None:
                        self.compensation_extractor = CompensationExtractor(
                            provider=self.llm_provider
                        )
                    
                    comp_data = self.compensation_extractor.extract_compensation(
                        compensation_raw
                    )
                    sections["compensation"] = comp_data
                except Exception as e:
                    print(f"  ⚠️  Error extracting compensation: {e}")
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
            print(f"Error getting job details for {job_data.get('id', 'unknown')}: {e}")
            if "row_element" in job_data:
                del job_data["row_element"]
            return job_data

    def save_job_to_folder(self, job_data, folder_name="geese"):
        """
        Save a job to a specific folder in WaterlooWorks

        Args:
            job_data: Job data dictionary (must have 'row_element' or be in details view)
            folder_name: Name of the folder to save to (default: "geese")

        Returns:
            bool: True if successful, False otherwise
        """
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
            self.close_job_details_panel()
            
            return True

        except Exception as e:
            print(f"  ❌ Error saving job to folder: {e}")
            return False
    
    def close_job_details_panel(self):
        """Close the currently open job details panel"""
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

    def scrape_current_page(
        self,
        include_details=False,
        existing_jobs=None,
        save_callback=None,
        all_jobs=None,
        save_every=5,
    ):
        """Scrape all jobs from the current page, skipping already-scraped jobs

        Args:
            include_details: Whether to deep scrape job details
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
            save_callback: Function to call for incremental saves
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
                        # Close the panel after getting details (batch mode)
                        self.close_job_details_panel()
                    else:
                        # Remove row_element if not getting details
                        if "row_element" in job_data:
                            del job_data["row_element"]
                    jobs.append(job_data)
                    new_jobs_count += 1

                    # Incremental save after every N new jobs
                    if (
                        save_callback
                        and save_every > 0
                        and new_jobs_count % save_every == 0
                    ):
                        all_jobs.extend(jobs)
                        jobs = []
                        print(
                            f"  💾 Auto-saving progress ({len(all_jobs)} jobs total)..."
                        )
                        save_callback(all_jobs)

        print(f"✅ Parsed {len(jobs)} jobs from this page ({new_jobs_count} new)\n")
        return jobs

    def scrape_all_jobs(
        self,
        include_details=False,
        existing_jobs=None,
        save_callback=None,
        save_every=5,
    ):
        """Scrape all jobs from all pages with incremental saving

        Args:
            include_details: Whether to deep scrape job details
            existing_jobs: Dict of {job_id: job_data} to skip already-scraped jobs
            save_callback: Function called periodically with accumulated jobs
            save_every: Save after this many new jobs scraped (default: 5)
        """
        if existing_jobs is None:
            existing_jobs = {}

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
            jobs = self.scrape_current_page(
                include_details=include_details,
                existing_jobs=existing_jobs,
                save_callback=save_callback,
                all_jobs=all_jobs,
                save_every=save_every,
            )
            all_jobs.extend(jobs)

            # Save progress after each page (in case save_every wasn't triggered)
            if save_callback:
                print(f"💾 Saving page progress ({len(all_jobs)} jobs total)...\n")
                save_callback(all_jobs)

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
