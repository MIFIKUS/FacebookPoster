from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


DEFAULT_TIMEOUT_SECONDS = 20


def wait_for_presence(driver: WebDriver, by: By, locator: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, locator)))


def wait_for_all_presence(driver: WebDriver, by: By, locator: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, locator)))
    except TimeoutException:
        return []


def wait_for_clickable(driver: WebDriver, by: By, locator: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, locator)))


def wait_and_click(driver: WebDriver, by: By, locator: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    element = wait_for_clickable(driver, by, locator, timeout)
    element.click()
    return element


def wait_and_type(driver: WebDriver, by: By, locator: str, text: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    el = wait_for_presence(driver, by, locator, timeout)
    el.clear()
    el.send_keys(text)
    return el


def wait_for_url_contains(driver: WebDriver, fragment: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
    return WebDriverWait(driver, timeout).until(EC.url_contains(fragment))


