"""Authentication helpers for WaterlooWorks sessions."""

from __future__ import annotations

from typing import Callable, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from modules.config import resolve_waterlooworks_credentials

# Timeout constants
TIMEOUT_SHORT = 10
TIMEOUT_MEDIUM = 30
TIMEOUT_LONG = 60


class WaterlooWorksAuth:
    """Handle authentication for WaterlooWorks."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        driver_factory: Optional[Callable[[], webdriver.Chrome]] = None,
        driver: Optional[webdriver.Chrome] = None,
    ) -> None:
        if driver is not None and driver_factory is not None:
            raise ValueError("Provide either an existing driver or a factory, not both.")

        resolved_username, resolved_password = resolve_waterlooworks_credentials(
            username, password, require=True
        )

        self.username = resolved_username
        self.password = resolved_password
        self.driver: Optional[webdriver.Chrome] = driver
        if driver is not None:
            self._driver_factory = driver_factory
        else:
            self._driver_factory = driver_factory or self._default_driver_factory
        self._owns_driver = driver is None

    @staticmethod
    def _default_driver_factory() -> webdriver.Chrome:
        """Create the default Selenium Chrome driver."""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        print("✅ Browser opened")
        return driver
        
    def login(self):
        """Log in to WaterlooWorks"""
        if not self.driver:
            if self._driver_factory is None:
                raise RuntimeError("No driver factory available to create a WebDriver instance.")

            self.driver = self._driver_factory()
            self._owns_driver = True
        
        print("🔑 Logging in to WaterlooWorks...")
        
        # Go to login page
        self.driver.get("https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login")
        
        # Enter email
        print("  → Entering email...")
        email_field = WebDriverWait(self.driver, TIMEOUT_SHORT).until(
            EC.presence_of_element_located((By.ID, "userNameInput"))
        )
        email_field.send_keys(self.username)
        self.driver.find_element(By.ID, "nextButton").click()
        
        # Enter password
        print("  → Entering password...")
        password_field = WebDriverWait(self.driver, TIMEOUT_SHORT).until(
            EC.presence_of_element_located((By.ID, "passwordInput"))
        )
        password_field.send_keys(self.password)
        self.driver.find_element(By.ID, "submitButton").click()
        
        # Wait for Duo 2FA
        print("\n⏳ Waiting for Duo 2FA (approve on your phone)...")
        trust_button = WebDriverWait(self.driver, TIMEOUT_LONG).until(
            EC.presence_of_element_located((By.ID, "trust-browser-button"))
        )
        trust_button.click()
        
        # Wait for WaterlooWorks to load
        WebDriverWait(self.driver, TIMEOUT_MEDIUM).until(
            EC.presence_of_element_located((By.XPATH, '//h1[text()="WaterlooWorks"]'))
        )
        
        print("✅ Login successful!\n")
        return True
    
    def close(self) -> None:
        """Close the browser, if owned by this instance."""
        if not self.driver:
            return

        if self._owns_driver:
            self.driver.quit()
            print("🔒 Browser closed")

        self.driver = None

    def __enter__(self) -> "WaterlooWorksAuth":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
