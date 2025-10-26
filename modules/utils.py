"""
Utility functions and constants for the scraper
"""

import re
import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Wait time constants
TIMEOUT = 10
PAGE_LOAD = 2

# Common CSS selectors (centralized)
SELECTORS = {
    "stat_card": ".simple--stat-card.border-radius--16.display--flex.flex--column.dist--between",
    "job_table": "table.table tbody tr",
    "pagination": ".pagination",
    "job_details_panel": ".is--long-form-reading",
    "close_panel_button": "[class='btn__default--text btn--default protip']",
    "floating_action_buttons": ".floating--action-bar.color--bg--default button",
}


def get_cell_text(cell, default="N/A"):
    """
    Safely extract text from a table cell with overflow--ellipsis class
    
    Args:
        cell: Selenium WebElement (table cell)
        default: Default value if extraction fails
        
    Returns:
        str: Extracted text or default value
    """
    try:
        elem = cell.find_element(By.CLASS_NAME, "overflow--ellipsis")
        text = elem.get_attribute("innerText")
        return text.strip() if text else default
    except Exception:
        return default


def calculate_chances(openings, applications):
    """
    Calculate chances ratio (openings/applications)
    
    Args:
        openings: Number of openings (str or int)
        applications: Number of applications (str or int)
        
    Returns:
        float: Chances ratio rounded to 3 decimals
    """
    try:
        openings_int = int(openings)
        applications_int = int(applications)
        return round(openings_int / applications_int, 3) if applications_int > 0 else 0.0
    except Exception:
        return 0.0


def sanitize_filename(text: str) -> str:
    """
    Sanitize text for use in filenames (Windows-compatible)
    
    Removes/replaces characters that are invalid in Windows filenames:
    < > : " / \ | ? *
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for filenames
    """
    text = text.replace('/', '_')
    text = text.replace('\\', '_')
    text = text.replace(':', '_')
    text = text.replace('*', '_')
    text = text.replace('?', '_')
    text = text.replace('"', '')
    text = text.replace('<', '')
    text = text.replace('>', '')
    text = text.replace('|', '_')
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace('{', '')
    text = text.replace('}', '')
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip().replace(' ', '_')
    text = re.sub(r'_+', '_', text)
    return text.strip('_')


def navigate_to_folder(driver, folder_name: str) -> bool:
    """
    Navigate to a specific WaterlooWorks folder (e.g., 'geese', 'saved jobs')
    
    Args:
        driver: Selenium WebDriver instance
        folder_name: Name of the folder to navigate to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        time.sleep(PAGE_LOAD)

        stat_cards = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELECTORS["stat_card"]))
        )

        target_card = None
        for card in stat_cards:
            if folder_name.lower() in card.text.lower():
                target_card = card
                break

        if not target_card:
            print(f"   ✗ Could not find '{folder_name}' folder")
            return False

        link = target_card.find_element(By.TAG_NAME, "a")
        link.click()
        time.sleep(PAGE_LOAD)
        return True
        
    except Exception as e:
        print(f"   ✗ Error navigating to '{folder_name}' folder: {e}")
        return False


def get_pagination_pages(driver) -> int:
    """
    Get the number of pages in pagination
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        Number of pages (minimum 1)
    """
    try:
        pagination = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
        return max(page_buttons, 1)
    except Exception:
        return 1


def go_to_next_page(driver):
    """
    Navigate to the next page in pagination
    
    Args:
        driver: Selenium WebDriver instance
    """
    pagination = WebDriverWait(driver, TIMEOUT).until(
        EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
    )
    next_button = pagination.find_elements(By.TAG_NAME, "li")[-2]
    next_button.find_element(By.TAG_NAME, "a").click()
    time.sleep(PAGE_LOAD)


def close_job_details_panel(driver) -> bool:
    """
    Close the currently open job details panel
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        close_buttons = driver.find_elements(By.CSS_SELECTOR, SELECTORS["close_panel_button"])
        if close_buttons:
            close_buttons[-1].click()
            time.sleep(1)
            return True
        return False
    except Exception:
        return False


def get_jobs_from_page(driver):
    """
    Get all job listings from the current page
    
    Returns:
        List of job row elements
    """
    try:
        time.sleep(PAGE_LOAD)
        job_rows = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELECTORS["job_table"]))
        )
        return job_rows
    except Exception as e:
        print(f"   ✗ Error reading jobs on page: {e}")
        return []
