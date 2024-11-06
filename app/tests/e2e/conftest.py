import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os


@pytest.fixture(scope="session")
def base_url():
    """Fixture for base URL of the application"""
    return os.getenv('APP_URL', 'http://localhost:5000')


@pytest.fixture(scope="function")
def driver():
    """Fixture for browser driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture(scope="function")
def wait(driver):
    """Fixture for WebDriverWait"""
    from selenium.webdriver.support.ui import WebDriverWait
    return WebDriverWait(driver, 10)