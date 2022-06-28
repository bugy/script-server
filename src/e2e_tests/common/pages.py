import random
import time
from abc import ABC

import conftest
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, \
    StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def is_displayed(element):
    try:
        WebDriverWait(conftest.browser, timeout=conftest.wait_time).until(EC.visibility_of(element))
        return True
    except (AttributeError, StaleElementReferenceException, TimeoutException):
        return False


def is_enabled(element):
    try:
        end_time = time.time() + conftest.wait_time
        while True:
            if element.is_enabled():
                return True
            time.sleep(1)
            if time.time() > end_time:
                break
    except (AttributeError, StaleElementReferenceException, TimeoutException):
        return False


def is_disabled(element):
    try:
        end_time = time.time() + conftest.wait_time
        while True:
            if not element.is_enabled():
                return True
            time.sleep(1)
            if time.time() > end_time:
                break
    except (AttributeError, StaleElementReferenceException, TimeoutException):
        return False


def get_parent_element(element):
    try:
        return element.find_element('xpath', '..')
    except (NoSuchElementException, ElementNotInteractableException):
        return None


def get_visible_values_of_list(element):
    try:
        return get_parent_element(element).find_element(By.CSS_SELECTOR,
                                                        "li:not([class*=\"header\"]):not(.search-hidden)")
    except (NoSuchElementException, ElementNotInteractableException):
        return None


def get_hidden_values_of_list(element):
    try:
        return get_parent_element(element).find_element(By.CSS_SELECTOR, "li:not([class*=\"header\"]).search-hidden")
    except (NoSuchElementException, ElementNotInteractableException):
        return None


def get_underline_error_text(element):
    try:
        return str(element.find_element('xpath', "..").get_attribute("data-error"))
    except (NoSuchElementException, ElementNotInteractableException):
        return None


class Page(ABC):
    browser: RemoteWebDriver

    def __init__(self, browser, host):
        self.browser = browser
        self.host = host
        self.url = ""

    def load(self):
        self.browser.get(self.host + self.url)

    @property
    def all_script_links(self):
        return self.browser.find_element(By.CSS_SELECTOR, "a.collection-item.script-list-item")

    def get_script_link_by_name(self, name):
        try:
            return self.browser.find_element_by_link_text(name)
        except (NoSuchElementException, ElementNotInteractableException):
            return None

    def get_scripts_group_by_name(self, name):
        try:
            return self.browser.find_element('xpath',
                                             "//span[contains(text(), '{}')]/parent::a[contains(@class,'collection-item')][contains(@class,'script-group')]".format(
                                                 name))
        except (NoSuchElementException, ElementNotInteractableException):
            return None

    def get_scripts_inside_group(self, group_link):
        try:
            return get_parent_element(group_link).find_element(By.CSS_SELECTOR, "a")
        except (NoSuchElementException, ElementNotInteractableException):
            return None

    def get_random_script_link(self):
        return random.choice(self.all_script_links)

    def find_element(self, selector, parent=None):
        try:
            if parent is not None:
                return parent.find_element(By.CSS_SELECTOR, selector)
            else:
                return self.browser.find_element(By.CSS_SELECTOR, selector)
        except (NoSuchElementException, ElementNotInteractableException):
            return None

    def find_input_by_label(self, label):
        try:
            return self.browser.find_element('xpath',
                                             "//label[contains(text(), '{}')]/parent::div//input".format(label))
        except (NoSuchElementException, ElementNotInteractableException):
            return None

    def execute_script(self):
        self.button_execute.click()
        time.sleep(3)
        return True

    def is_404_page(self):
        return self.find_element("body.cms-no-route") is not None

    @property
    def sidebar(self):
        return self.find_element(".main-app-sidebar")

    @property
    def sidebar_header(self):
        return self.find_element(".main-app-sidebar .header")

    @property
    def sidebar_scripts_list(self):
        return self.find_element(".main-app-sidebar .scripts-list.collection")

    @property
    def sidebar_history_button(self):
        return self.find_element(".main-app-sidebar .history-button")

    @property
    def sidebar_search_button(self):
        return self.find_element(".main-app-sidebar .search-button")

    @property
    def sidebar_header_link(self):
        return self.find_element(".main-app-sidebar .header-link")

    @property
    def main_app_content(self):
        return self.find_element(".main-app-content")

    @property
    def script_header(self):
        return self.find_element(".script-header")

    @property
    def actions_panel(self):
        return self.find_element(".actions-panel")

    @property
    def button_execute(self):
        return self.find_element(".button-execute")

    @property
    def button_stop(self):
        return self.find_element(".button-stop")

    @property
    def script_description(self):
        return self.find_element(".script-description")

    @property
    def script_parameters_panel(self):
        return self.find_element(".script-parameters-panel")

    @property
    def log(self):
        return self.find_element(".main-app-content code.log-content")

    @property
    def users_input(self):
        return self.find_element("input.script-input-field")

    @property
    def executor_tabs(self):
        return self.browser.find_element(By.CSS_SELECTOR, ".tab.executor-tab")

    @property
    def active_executor_tab(self):
        return self.find_element(".btn-flat.active")

    @property
    def add_new_tab_button(self):
        return self.find_element(".tab [title='Add another script instance']")


class VeryParametrizedScript(Page):
    browser: RemoteWebDriver

    def __init__(self, browser, host):
        self.browser = browser
        self.host = host
        self.url = "index.html#/Very%20parameterized"

    @property
    def parameter_simple_boolean(self):
        return self.find_element("[title='Boolean One'] input[type='checkbox']")

    @property
    def parameter_simple_boolean_label(self):
        return self.find_element("[title='Boolean One'] span")

    @property
    def parameter_simple_int(self):
        return self.find_input_by_label('Simple Int')

    @property
    def parameter_simple_text(self):
        return self.find_input_by_label('Simple Text')

    @property
    def parameter_simple_list(self):
        return self.find_input_by_label('Simple List')

    @property
    def parameter_simple_list_drop_down(self):
        return self.find_element("ul.dropdown-content.select-dropdown", get_parent_element(self.parameter_simple_list))

    @property
    def parameter_simple_list_drop_down_elements(self):
        return self.parameter_simple_list_drop_down.find_element(By.CSS_SELECTOR, "li[id^=\"select-options\"]")

    @property
    def parameter_file_upload(self):
        return self.find_input_by_label('File upload')

    @property
    def parameter_multiple_selection(self):
        return self.find_input_by_label('Multiple selection')

    @property
    def parameter_required_text(self):
        return self.find_input_by_label('Required Text')

    @property
    def parameter_required_list(self):
        return self.find_input_by_label('Required List')

    @property
    def parameter_required_list_drop_down(self):
        return self.find_element("ul.dropdown-content.select-dropdown", self.parameter_required_list)

    @property
    def parameter_required_list_drop_down_elements(self):
        return self.parameter_required_list.find_element(By.CSS_SELECTOR, "li[id^=\"select-options\"]")

    @property
    def parameter_constrained_int(self):
        return self.find_input_by_label('Constrained Int')

    @property
    def parameter_default_text(self):
        return self.find_input_by_label('Default Text')

    @property
    def parameter_default_boolean(self):
        return self.find_element("[title='Boolean Two'] input[type='checkbox']")

    @property
    def parameter_default_boolean_label(self):
        return self.find_element("[title='Boolean Two'] span")

    @property
    def parameter_command_based_list(self):
        return self.find_input_by_label('Command-based list')

    @property
    def command_based_list(self):
        return self.find_element("ul[id^=\"select-options\"]", get_parent_element(self.parameter_command_based_list))

    @property
    def search_field_in_command_based_list(self):
        return self.find_element("div.input-field.combobox-search input", get_parent_element(self.parameter_command_based_list))

    @property
    def parameter_secure_int(self):
        return self.find_input_by_label('Secure Int')

    @property
    def parameter_secure_list(self):
        return self.find_input_by_label('Secure List')

    @property
    def parameter_very_long_list(self):
        return self.find_input_by_label('Very long list')

    @property
    def parameter_multiselect_as_secure_arguments(self):
        return self.find_input_by_label('Multiselect as secure arguments')

    @property
    def parameter_dependant_list(self):
        return self.find_input_by_label('Dependant list')

    @property
    def parameter_auth_username(self):
        return self.find_input_by_label('Auth username')

    @property
    def parameter_any_ip(self):
        return self.find_input_by_label('Any IP')

    @property
    def parameter_ip_v4(self):
        return self.find_input_by_label('IP v4')

    @property
    def parameter_ip_v6(self):
        return self.find_input_by_label('IP v6')

    @property
    def parameter_server_file(self):
        return self.find_input_by_label('Server file')

    @property
    def parameter_recursive_file(self):
        return self.find_input_by_label('Recursive file')

    @property
    def parameter_inc_param1(self):
        return self.find_input_by_label('inc_param1')

    @property
    def parameter_inc_param2(self):
        return self.find_input_by_label('inc_param2')


class DestroyWorldScript(Page):
    browser: RemoteWebDriver

    def __init__(self, browser, host):
        self.browser = browser
        self.host = host
        self.url = "index.html#/destroy_world"

    @property
    def first_step_log_content(self):
        return ("<br><div>Stars are born, they live, and they die. The sun is no different, and when it goes, the Earth goes with</div><div>it. But our planet won't go quietly into the night.</div><br><div>Want to continue? Y/N</div>")

    @property
    def second_step_log_content(self):
        return ("<div>Y</div><div>Rather, when the sun expands into a red giant during the throes of death, it will vaporize the Earth.</div><br><div>Want to continue? Y/N</div>")

    @property
    def no_exit_log_content(self):
        return ("<div>N</div><div>Bye bye!</div>")
