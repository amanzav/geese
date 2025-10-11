"""
Authentication Module for Geese
Handles WaterlooWorks login
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WaterlooWorksAuth:
    """Handle authentication for WaterlooWorks"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        
    def _init_driver(self):
        """Initialize Chrome browser"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        print("✅ Browser opened")
        
    def login(self):
        """Log in to WaterlooWorks"""
        if not self.driver:
            self._init_driver()
        
        print("🔑 Logging in to WaterlooWorks...")
        
        # Go to login page
        self.driver.get("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
        
        # Enter email
        print("  → Entering email...")
        email_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "userNameInput"))
        )
        email_field.send_keys(self.username)
        self.driver.find_element(By.ID, "nextButton").click()
        
        # Enter password
        print("  → Entering password...")
        password_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "passwordInput"))
        )
        password_field.send_keys(self.password)
        self.driver.find_element(By.ID, "submitButton").click()
        
        # Wait for Duo 2FA
        print("\n⏳ Waiting for Duo 2FA (approve on your phone)...")
        trust_button = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.ID, "trust-browser-button"))
        )
        trust_button.click()
        
        # Wait for WaterlooWorks to load
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="WaterlooWorks"]'))
        )
        
        print("✅ Login successful!\n")
        return True
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")
