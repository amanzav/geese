"""Unit tests for the WaterlooWorks authentication wrapper."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

# Ensure repository modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent))


class _By:
    ID = "id"
    XPATH = "xpath"


class _ChromeOptions:
    def __init__(self):
        self.arguments = []

    def add_argument(self, argument):
        self.arguments.append(argument)


class _Chrome:
    def __init__(self, *_, **__):
        raise RuntimeError("Stub Chrome driver should not be instantiated during tests.")


def _presence_of_element_located(locator):
    def _predicate(driver):
        return driver.find_element(*locator)

    return _predicate


selenium_module = types.ModuleType("selenium")
webdriver_module = types.ModuleType("selenium.webdriver")
webdriver_module.ChromeOptions = _ChromeOptions
webdriver_module.Chrome = _Chrome

common_module = types.ModuleType("selenium.webdriver.common")
by_module = types.ModuleType("selenium.webdriver.common.by")
by_module.By = _By

support_module = types.ModuleType("selenium.webdriver.support")
support_ui_module = types.ModuleType("selenium.webdriver.support.ui")
support_ui_module.WebDriverWait = None
support_ec_module = types.ModuleType("selenium.webdriver.support.expected_conditions")
support_ec_module.presence_of_element_located = _presence_of_element_located
support_module.expected_conditions = support_ec_module

selenium_module.webdriver = webdriver_module
webdriver_module.common = common_module
webdriver_module.support = support_module
common_module.by = by_module
support_module.ui = support_ui_module
support_module.common = common_module
support_module.expected_conditions = support_ec_module

dotenv_module = types.ModuleType("dotenv")
dotenv_module.load_dotenv = lambda *_, **__: False

sys.modules.setdefault("selenium", selenium_module)
sys.modules.setdefault("selenium.webdriver", webdriver_module)
sys.modules.setdefault("selenium.webdriver.common", common_module)
sys.modules.setdefault("selenium.webdriver.common.by", by_module)
sys.modules.setdefault("selenium.webdriver.support", support_module)
sys.modules.setdefault("selenium.webdriver.support.ui", support_ui_module)
sys.modules.setdefault("selenium.webdriver.support.expected_conditions", support_ec_module)
sys.modules.setdefault("dotenv", dotenv_module)

from selenium.webdriver.common.by import By

from modules.auth import WaterlooWorksAuth


class StubElement:
    def __init__(self):
        self.value = ""
        self.clicked = False

    def send_keys(self, value):
        self.value = value

    def click(self):
        self.clicked = True


class StubDriver:
    def __init__(self):
        self.visited_urls = []
        self.closed = False
        self.elements = {
            (By.ID, "userNameInput"): StubElement(),
            (By.ID, "nextButton"): StubElement(),
            (By.ID, "passwordInput"): StubElement(),
            (By.ID, "submitButton"): StubElement(),
            (By.ID, "trust-browser-button"): StubElement(),
            (By.XPATH, '//h1[text()="WaterlooWorks"]'): StubElement(),
        }

    def get(self, url):
        self.visited_urls.append(url)

    def find_element(self, by, value):
        return self.elements[(by, value)]

    def maximize_window(self):
        pass

    def quit(self):
        self.closed = True


class DummyWait:
    def __init__(self, driver):
        self.driver = driver

    def until(self, condition):
        return condition(self.driver)


@pytest.fixture(autouse=True)
def patch_webdriver_wait(monkeypatch):
    monkeypatch.setattr("modules.auth.WebDriverWait", lambda driver, timeout: DummyWait(driver))
    return monkeypatch


def test_login_uses_injected_driver_factory():
    driver = StubDriver()
    factory_calls = {"count": 0}

    def factory():
        factory_calls["count"] += 1
        return driver

    auth = WaterlooWorksAuth("user@example.com", "password", driver_factory=factory)

    auth.login()

    assert factory_calls["count"] == 1
    assert driver.visited_urls[-1] == "https://waterlooworks.uwaterloo.ca/waterloo.htm?action=login"
    assert driver.elements[(By.ID, "userNameInput")].value == "user@example.com"
    assert driver.elements[(By.ID, "nextButton")].clicked is True
    assert driver.elements[(By.ID, "passwordInput")].value == "password"
    assert driver.elements[(By.ID, "submitButton")].clicked is True
    assert driver.elements[(By.ID, "trust-browser-button")].clicked is True

    auth.close()
    assert driver.closed is True


def test_context_manager_closes_owned_driver():
    driver = StubDriver()

    def factory():
        return driver

    auth = WaterlooWorksAuth("user@example.com", "password", driver_factory=factory)

    with pytest.raises(RuntimeError):
        with auth as session:
            session.login()
            raise RuntimeError("boom")

    assert driver.closed is True


def test_close_does_not_quit_unowned_driver():
    driver = StubDriver()
    auth = WaterlooWorksAuth("user@example.com", "password", driver=driver)

    auth.login()
    auth.close()

    assert driver.closed is False
