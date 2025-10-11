"""
Scraper Module for Geese
Handles job scraping and navigation on WaterlooWorks
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Wait time constants
TIMEOUT_DEFAULT = 10
PAGE_LOAD_WAIT = 2


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
        """
        Navigate to the all jobs page and apply filters
        
        Args:
            program_filter_value (str): Program filter checkbox value (e.g., "38688")
        """
        print("📋 Navigating to jobs page...")
        
        self.driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        time.sleep(PAGE_LOAD_WAIT)
        
        print("🔘 Clicking initial filter button...")
        filter_button = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.doc-viewer--filter-bar button')
            )
        )
        filter_button.click()
        time.sleep(PAGE_LOAD_WAIT)
        
        # Apply program filter if provided
        if program_filter_value:
            print(f"🎯 Applying program filter ({program_filter_value})...")
            
            # Click the filter menu button
            filter_menu_button = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.btn__default.btn--black.tag-rail__menu-btn')
                )
            )
            filter_menu_button.click()
            time.sleep(PAGE_LOAD_WAIT)
            
            # Find and click the program checkbox using JavaScript (to avoid click interception)
            program_checkbox = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f'.color--bg--white.doc-viewer input[value="{program_filter_value}"]')
                )
            )
            
            # Use JavaScript click to bypass the covering label
            self.driver.execute_script("arguments[0].click();", program_checkbox)
            time.sleep(PAGE_LOAD_WAIT)
            
            # Close the sidebar using JavaScript
            close_button = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.js--btn--close-sidebar')
                )
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            time.sleep(PAGE_LOAD_WAIT)
            
            print("✅ Program filter applied\n")
        else:
            print("✅ Jobs page loaded (no filter applied)\n")
    
    def get_job_table(self):
        """
        Get all rows from the current job listings table
        
        Returns:
            list: List of table rows (excluding header)
        """
        print("📊 Getting job listings...")
        
        table = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "data-viewer-table"))
        )
        
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
        print(f"✅ Found {len(rows)} jobs on this page\n")
        return rows
    
    def get_pagination_pages(self):
        """
        Get the number of pages in the current view
        
        Returns:
            int: Number of pages
        """
        pagination = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        
        page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
        return page_buttons
    
    def next_page(self):
        """Go to the next page in pagination"""
        pagination = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        
        next_button = pagination.find_elements(By.TAG_NAME, "li")[-2]
        next_button.find_element(By.TAG_NAME, "a").click()
        time.sleep(PAGE_LOAD_WAIT)
