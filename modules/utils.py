"""
Utility functions and constants for the scraper
"""

from selenium.webdriver.common.by import By

# Wait time constants
TIMEOUT = 10
PAGE_LOAD = 2


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
