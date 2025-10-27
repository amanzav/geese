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
    try:
        elem = cell.find_element(By.CLASS_NAME, "overflow--ellipsis")
        text = elem.get_attribute("innerText")
        return text.strip() if text else default
    except Exception as e:
        return default


def calculate_chances(openings, applications):
    try:
        openings_int = int(openings)
        applications_int = int(applications)
        return round(openings_int / applications_int, 3) if applications_int > 0 else 0.0
    except Exception as e:
        return 0.0


def sanitize_filename(text: str) -> str:
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
    try:
        pagination = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
        return max(page_buttons, 1)
    except Exception as e:
        return 1


def go_to_next_page(driver):
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
    try:
        close_buttons = driver.find_elements(By.CSS_SELECTOR, SELECTORS["close_panel_button"])
        if close_buttons:
            close_buttons[-1].click()
            time.sleep(1)
            return True
        return False
    except Exception as e:
        return False


def get_jobs_from_page(driver):
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
    except Exception as e:
        return False


def click_and_wait(driver, element, wait_for=None, max_wait=None):
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
    if timeout is None:
        timeout = WaitTimes.FAST
        
    try:
        return WebDriverWait(driver, timeout, poll_frequency=0.05).until(
            EC.presence_of_element_located((by, selector))
        )
    except Exception as e:
        return None


# Performance monitoring helper
from contextlib import contextmanager

@contextmanager
def timer(operation_name: str):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"⏱️  {operation_name} took {elapsed:.2f}s")

