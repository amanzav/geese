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
    
    def go_to_jobs_page(self):
        """Navigate to the all jobs page and click the filter button"""
        print("📋 Navigating to jobs page...")
        
        self.driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        time.sleep(PAGE_LOAD_WAIT)
        
        print("🔘 Clicking filter button...")
        filter_button = WebDriverWait(self.driver, TIMEOUT_DEFAULT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.doc-viewer--filter-bar button')
            )
        )
        filter_button.click()
        
        print("✅ Jobs page loaded\n")
        time.sleep(PAGE_LOAD_WAIT)
    
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
