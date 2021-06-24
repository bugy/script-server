from common.pages import VeryParametrizedScript
import allure
from common.pages import is_displayed, is_enabled, get_parent_element, get_underline_error_text, get_hidden_values_of_list, get_visible_values_of_list
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level
import string
import random
import sys
from selenium.webdriver.common.keys import Keys

search_request = "lo"


@severity(severity_level.NORMAL)
@allure.title("Check presented elements in app section")
def test_elements_in_app_section(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    very_parametrized_script_page.load()

    expect(is_displayed(very_parametrized_script_page.script_description), "Script description not found")
    expect(is_displayed(very_parametrized_script_page.script_parameters_panel), "Parameters panel not found")
    expect(is_displayed(very_parametrized_script_page.button_execute), "Execute button not found")
    expect(is_enabled(very_parametrized_script_page.button_execute), "Execute button not enabled")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check presented parameters")
def test_params(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    expect(is_displayed(very_parametrized_script_page.parameter_simple_int), "Simple int param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_simple_boolean_label), "Simple boolean param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_simple_text), "Simple text param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_simple_list), "Simple list param not found")
    expect(very_parametrized_script_page.parameter_file_upload is not None, "File upload param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_multiple_selection), "Multiple selection param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_required_text), "Required text param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_required_list), "Required list param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_constrained_int), "Constrained int param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_default_text), "Default text param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_default_boolean_label), "Default boolean param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_command_based_list), "Command based list param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_secure_list), "Secure list param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_secure_int), "Secure int param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_very_long_list), "Very long list param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_multiselect_as_secure_arguments), "Multiselect as secure arguments param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_dependant_list), "Dependant list param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_auth_username), "Auth username param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_any_ip), "Any IP param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_ip_v4), "IP v4 param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_ip_v6), "IP v6 param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_server_file), "Server file param not found")
    expect(is_displayed(very_parametrized_script_page.parameter_recursive_file), "Recursive file param not found")

    expect(not is_displayed(very_parametrized_script_page.parameter_inc_param1), "inc_param1 is displayed by default ")
    expect(not is_displayed(very_parametrized_script_page.parameter_inc_param2), "inc_param2 is displayed by defaukt")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check Default boolean is checked by default")
def test_default_boolean(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    assert very_parametrized_script_page.parameter_default_boolean.is_selected(), "Default boolean is not selected"


@severity(severity_level.NORMAL)
@allure.title("Uncheck Default boolean")
def test_uncheck_default_boolean(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    very_parametrized_script_page.parameter_default_boolean_label.click()

    assert not very_parametrized_script_page.parameter_default_boolean.is_selected(), "Default boolean is selected"


@severity(severity_level.NORMAL)
@allure.title("Check Simple boolean is unchecked by default")
def test_simple_boolean(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    assert not very_parametrized_script_page.parameter_simple_boolean.is_selected(), "Default boolean is not selected"


@severity(severity_level.NORMAL)
@allure.title("Check Simple boolean")
def test_check_simple_boolean(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    very_parametrized_script_page.parameter_simple_boolean_label.click()

    assert very_parametrized_script_page.parameter_simple_boolean.is_selected(), "Default boolean is selected"


@severity(severity_level.NORMAL)
@allure.title("Simple int is empty by default")
def test_check_simple_int_by_default(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    assert very_parametrized_script_page.parameter_simple_int.text == "", "Simple int is not empty by default"


@severity(severity_level.NORMAL)
@allure.title("Try to input string in simple int")
def test_input_string_in_simple_int(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    very_parametrized_script_page.parameter_simple_int.send_keys("String value" + Keys.ENTER)
    assert get_underline_error_text(very_parametrized_script_page.parameter_simple_int) == "integer expected"


@severity(severity_level.NORMAL)
@allure.title("Try to input int in simple int")
def test_input_int_in_simple_int(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    random_int = random.randint(0, sys.maxsize)

    very_parametrized_script_page.parameter_simple_int.clear()
    very_parametrized_script_page.parameter_simple_int.send_keys(str(random_int) + Keys.ENTER)
    expect(very_parametrized_script_page.parameter_simple_int.get_attribute("class") == "validate valid", "Class is not valid")
    expect(very_parametrized_script_page.parameter_simple_int.get_attribute('value') == str(random_int), "Field text is not equal to input")
    expect(get_underline_error_text(very_parametrized_script_page.parameter_simple_int) == "", "Underline text error is not empty: " + str(get_underline_error_text(very_parametrized_script_page.parameter_simple_int)))

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Input random string in simple text")
def test_input_text_in_simple_text(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    random_srting = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 254)))
    very_parametrized_script_page.parameter_simple_text.send_keys(random_srting)

    expect(very_parametrized_script_page.parameter_simple_text.get_attribute('value') == str(random_srting), "Field text is not equal to input")
    expect(get_underline_error_text(very_parametrized_script_page.parameter_simple_text) == "", "Underline text error is not empty: " + str(get_underline_error_text(very_parametrized_script_page.parameter_simple_text)))

    very_parametrized_script_page.parameter_simple_text.send_keys(Keys.ENTER)
    expect(very_parametrized_script_page.parameter_simple_text.get_attribute("class") == "validate valid", "Class is not valid")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Input key text in simple text")
def test_input_key_text_in_simple_text(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    very_parametrized_script_page.parameter_simple_text.clear()
    very_parametrized_script_page.parameter_simple_text.send_keys("included")

    expect(is_displayed(very_parametrized_script_page.parameter_inc_param1), "inc_param1 is not displayed. Simple text value is: " + str(very_parametrized_script_page.parameter_simple_text.get_attribute('value')))
    expect(is_displayed(very_parametrized_script_page.parameter_inc_param2), "inc_param2 is not displayed. Simple text value is: " + str(very_parametrized_script_page.parameter_simple_text.get_attribute('value')))

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Edit appeared inc_params")
def test_input_text_in_inc_params(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    random_srting1 = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 254)))
    very_parametrized_script_page.parameter_inc_param1.send_keys(random_srting1)
    random_srting2 = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 254)))
    very_parametrized_script_page.parameter_inc_param2.send_keys(random_srting2)
    expect(very_parametrized_script_page.parameter_inc_param1.get_attribute('value') == str(random_srting1), "Field text is not equal to input")
    expect(get_underline_error_text(very_parametrized_script_page.parameter_inc_param1) == "", "Underline text error is not empty: " + str(get_underline_error_text(very_parametrized_script_page.parameter_inc_param1)))
    very_parametrized_script_page.parameter_inc_param1.send_keys(Keys.ENTER)
    expect(very_parametrized_script_page.parameter_inc_param1.get_attribute("class") == "validate valid", "Class is not valid")
    expect(very_parametrized_script_page.parameter_inc_param2.get_attribute('value') == str(random_srting2), "Field text is not equal to input")
    expect(get_underline_error_text(very_parametrized_script_page.parameter_inc_param2) == "", "Underline text error is not empty: " + str(get_underline_error_text(very_parametrized_script_page.parameter_inc_param2)))
    very_parametrized_script_page.parameter_inc_param2.send_keys(Keys.ENTER)
    expect(very_parametrized_script_page.parameter_inc_param2.get_attribute("class") == "validate valid", "Class is not valid")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Edit simple text to hide inc_params")
def test_edit_simple_text_to_hide_inc_params(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)

    very_parametrized_script_page.parameter_simple_text.send_keys("something")

    expect(not is_displayed(very_parametrized_script_page.parameter_inc_param1), "inc_param1 is displayed while not key text is in simple text field is presented")
    expect(not is_displayed(very_parametrized_script_page.parameter_inc_param2), "inc_param2 is displayed while not key text is in simple text field is presented")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Open drop-down for simple list parameter")
def test_click_simple_list(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    very_parametrized_script_page.parameter_simple_list.click()

    expect(is_displayed(very_parametrized_script_page.parameter_simple_list_drop_down), "Drop down on list parameter click was not opened")
    expect(len(very_parametrized_script_page.parameter_simple_list_drop_down_elements) > 0, "Drop down list has no elements")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Select random element from drop-down list")
def test_click_random_drop_down_element(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    random_drop_down_element = random.choice(very_parametrized_script_page.parameter_simple_list_drop_down_elements)
    random_drop_down_element.click()
    expect(str(very_parametrized_script_page.parameter_simple_list.get_attribute('value')) == str(random_drop_down_element.get_attribute('title')), "Field text is not equal to input")
    expect(random_drop_down_element.get_attribute("class").find("selected") > -1, "Selected element has not class \"selected\"")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Open drop-down for command based list parameter")
def test_click_command_based_list(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    very_parametrized_script_page.parameter_command_based_list.click()

    expect(is_displayed(very_parametrized_script_page.command_based_list), "Command based List was not opened on click")
    expect(is_displayed(very_parametrized_script_page.search_field_in_command_based_list), "Search field in command based list was not opened on click")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Search in command based list parameter")
def test_search_in_command_based_list(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    very_parametrized_script_page.search_field_in_command_based_list.send_keys(search_request)

    expect(is_displayed(very_parametrized_script_page.command_based_list), "Command based List is not displayed after search")
    for element in get_visible_values_of_list(very_parametrized_script_page.command_based_list):
        expect(is_displayed(element), "Visible list element is not displayed")
    for element in get_hidden_values_of_list(very_parametrized_script_page.command_based_list):
        expect(not is_displayed(element), "Hidden list element is not displayed")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Search in command based list parameter")
def test_check_search_results_in_command_based_list(browser, config_host):
    very_parametrized_script_page = VeryParametrizedScript(browser, config_host)
    for element in get_visible_values_of_list(very_parametrized_script_page.command_based_list):
        expect(str(element.text).find(search_request) > -1)

    assert_expectations()
