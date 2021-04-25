import json
import time

import allure
import pytest
from selenium.webdriver import Chrome, Firefox, Ie
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

CONFIG_PATH = 'input/config.json'
DEFAULT_WAIT_TIME = 10
SUPPORTED_BROWSERS = ['chrome', 'firefox', 'ie']
DEFAULT_HEADLESS_MODE = True
DEFAULT_SCREENSHOTS_NEEDED = False
DEFAULT_DISPLAYED_SCRIPTS = ["Bash formatting", "colortest", "destroy_world", "Download kittens", "Multiple words", "Very parameterized", "Write to file (WIN)"]


with open(CONFIG_PATH) as config_file:
    config = json.load(config_file)

wait_time = int(config['wait_time']) if 'wait_time' in config else DEFAULT_WAIT_TIME
session_start_time = time.time()


@pytest.fixture(scope='session')
def config_browser():
    if 'browser' not in config:
        raise Exception('The config file does not contain "browser"')
    elif config['browser'] not in SUPPORTED_BROWSERS:
        raise Exception(f'"{config["browser"]}" is not a supported browser')
    return config['browser']


@pytest.fixture(scope='session', autouse=True)
def config_host():
    return str(config['host']) if 'host' in config else ""


@pytest.fixture(scope='session')
def config_headless_mode():
    return bool(config['headless_mode']) if 'headless_mode' in config else DEFAULT_HEADLESS_MODE


@pytest.fixture(scope='session')
def scripts():
    return (config['scripts']) if 'scripts' in config else DEFAULT_DISPLAYED_SCRIPTS


@pytest.fixture(scope='module')
def browser(config_browser, config_headless_mode, request):
    if config_browser == 'chrome':
        options = ChromeOptions()
        options.headless = config_headless_mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # mobile_emulation = {"deviceName": "Nexus 5"}
        # options.add_experimental_option("mobileEmulation", mobile_emulation)
        driver = Chrome(options=options)
    elif config_browser == 'firefox':
        options = FirefoxOptions()
        options.headless = config_headless_mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = Firefox(options=options)
    elif config_browser == 'ie':
        if config_headless_mode:
            Warning("Headless mode is not supported in IE")
        driver = Ie()
    else:
        raise Exception(f'"{config_browser}" is not a supported browser')
    driver.delete_all_cookies()
    driver.set_window_size(1920, 1080)
    driver.implicitly_wait(wait_time)

    # Return the driver object at the end of setup
    yield driver

    # For cleanup, quit the driver
    driver.quit()


def pytest_configure(config):
    with open(CONFIG_PATH) as config_file:
        data = json.load(config_file)
    for config_item in data.keys():
        config._metadata[str(config_item)] = str(data[config_item])


def pytest_html_report_title(report):
    report.title = "Report"


def get_report_status(report):
    if report.failed:
        status = "FAILED"
    elif report.passed:
        status = "PASSED"
    elif report.skipped:
        status = "SKIPPED"
    else:
        status = "UNKNOWN_STATUS"
    return status


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call':
        request = item.funcargs['request']
        driver = request.getfixturevalue('browser')
        allure.attach(driver.get_screenshot_as_png(), attachment_type=allure.attachment_type.PNG)
        allure.attach(driver.page_source, attachment_type=allure.attachment_type.TEXT)
