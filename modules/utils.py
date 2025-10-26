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
PAGE_LOAD = 0.5  # Optimized from 2s to 0.5s


# ============================================
# PERFORMANCE OPTIMIZATION UTILITIES
# ============================================

class WaitTimes:
    """Configurable wait times for different operation types"""
    INSTANT = 0.05     # Immediate DOM updates
    FAST = 0.3         # Simple page updates
    MEDIUM = 0.8       # Modal/dialog loading
    SLOW = 1.5         # Full page loads
    USER_INPUT = 10.0  # Waiting for user action

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
    r"""
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
    Navigate to a specific WaterlooWorks folder - OPTIMIZED
    
    Args:
        driver: Selenium WebDriver instance
        folder_name: Name of the folder to navigate to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        driver.get("https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm")
        
        # Smart wait for stat cards
        if not smart_page_wait(
            driver, 
            (By.CSS_SELECTOR, SELECTORS["stat_card"]),
            max_wait=WaitTimes.SLOW
        ):
            print(f"   ✗ Page did not load properly")
            return False

        stat_cards = driver.find_elements(By.CSS_SELECTOR, SELECTORS["stat_card"])

        target_card = None
        for card in stat_cards:
            if folder_name.lower() in card.text.lower():
                target_card = card
                break

        if not target_card:
            print(f"   ✗ Could not find '{folder_name}' folder")
            return False

        link = target_card.find_element(By.TAG_NAME, "a")
        click_and_wait(driver, link, max_wait=WaitTimes.MEDIUM)
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
    Navigate to the next page in pagination - OPTIMIZED
    
    Args:
        driver: Selenium WebDriver instance
    """
    try:
        pagination = fast_presence_check(driver, ".pagination", by=By.CLASS_NAME, timeout=TIMEOUT)
        if not pagination:
            print("   ⚠️  Pagination not found")
            return
        
        next_button_li = pagination.find_elements(By.TAG_NAME, "li")[-2]
        next_link = next_button_li.find_element(By.TAG_NAME, "a")
        
        click_and_wait(
            driver, 
            next_link,
            wait_for=(By.CSS_SELECTOR, SELECTORS["job_table"]),
            max_wait=WaitTimes.MEDIUM
        )
    except Exception as e:
        print(f"   ⚠️  Error going to next page: {e}")


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


# ============================================
# SMART WAIT HELPERS
# ============================================

def smart_page_wait(driver, expected_element=None, max_wait=None, poll=0.1):
    """
    Intelligent wait that returns as soon as page is ready.
    
    Args:
        driver: Selenium WebDriver
        expected_element: Optional tuple (By.X, "selector") to wait for
        max_wait: Maximum time to wait (defaults to WaitTimes.SLOW)
        poll: Polling frequency (check every X seconds)
        
    Returns:
        bool: True if successful, False if timeout
        
    Example:
        # Wait for specific element
        smart_page_wait(driver, (By.CLASS_NAME, "job-table"), max_wait=2.0)
        
        # Wait for page ready
        smart_page_wait(driver)
    """
    if max_wait is None:
        max_wait = WaitTimes.SLOW
        
    try:
        if expected_element:
            WebDriverWait(driver, max_wait, poll_frequency=poll).until(
                EC.presence_of_element_located(expected_element)
            )
        else:
            # Wait for document ready state
            WebDriverWait(driver, max_wait, poll_frequency=poll).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        return True
    except Exception:
        return False


def click_and_wait(driver, element, wait_for=None, max_wait=None):
    """
    Click element and optionally wait for expected condition.
    
    Args:
        driver: Selenium WebDriver
        element: Element to click (WebElement)
        wait_for: Optional (By.X, "selector") tuple for element to appear after click
        max_wait: Maximum wait time (defaults to WaitTimes.FAST)
        
    Returns:
        bool: True if successful
        
    Example:
        # Click button and wait for modal to appear
        button = driver.find_element(By.ID, "submit")
        click_and_wait(driver, button, wait_for=(By.CLASS_NAME, "modal"))
    """
    if max_wait is None:
        max_wait = WaitTimes.FAST
        
    try:
        driver.execute_script("arguments[0].click();", element)
        
        if wait_for:
            return smart_page_wait(driver, wait_for, max_wait)
        else:
            time.sleep(WaitTimes.INSTANT)  # Minimal delay for DOM update
        
        return True
    except Exception as e:
        print(f"   ⚠️  Click failed: {e}")
        return False


def smart_element_click(driver, element, scroll_first=True):
    """
    Reliably click element with smart scrolling and minimal waits.
    
    Args:
        driver: Selenium WebDriver
        element: Element to click
        scroll_first: Whether to scroll element into view
        
    Returns:
        bool: True if successful
        
    Example:
        link = row.find_element(By.TAG_NAME, "a")
        smart_element_click(driver, link)
    """
    try:
        if scroll_first:
            # Scroll to center with instant behavior
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});",
                element
            )
        
        # Wait for element to be clickable (fast poll)
        WebDriverWait(driver, 2, poll_frequency=0.05).until(
            EC.element_to_be_clickable(element)
        )
        
        # JavaScript click for reliability
        driver.execute_script("arguments[0].click();", element)
        time.sleep(WaitTimes.INSTANT)
        
        return True
    except Exception as e:
        print(f"   ⚠️  Smart click failed: {e}")
        return False


def fast_presence_check(driver, selector, by=By.CSS_SELECTOR, timeout=None):
    """
    Quickly check if element is present with fast polling.
    
    Args:
        driver: Selenium WebDriver
        selector: Element selector
        by: Selenium By type (default: By.CSS_SELECTOR)
        timeout: Maximum wait time (defaults to WaitTimes.FAST)
        
    Returns:
        WebElement or None
        
    Example:
        modal = fast_presence_check(driver, ".modal-dialog")
        if modal:
            # Modal found
    """
    if timeout is None:
        timeout = WaitTimes.FAST
        
    try:
        return WebDriverWait(driver, timeout, poll_frequency=0.05).until(
            EC.presence_of_element_located((by, selector))
        )
    except Exception:
        return None


# Performance monitoring helper
from contextlib import contextmanager

@contextmanager
def timer(operation_name: str):
    """
    Context manager to time operations
    
    Usage:
        with timer("Scraping 10 jobs"):
            scraper.scrape_current_page()
    """
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"⏱️  {operation_name} took {elapsed:.2f}s")

