from common.pages import DestroyWorldScript
from selenium.webdriver.common.keys import Keys
import allure
from common.pages import is_displayed, is_enabled, is_disabled
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level
import time


@severity(severity_level.NORMAL)
@allure.title("Check presented elements in app section")
def test_elements_in_app_section(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)
    destroy_world_script_page.load()

    expect(is_displayed(destroy_world_script_page.script_description), "Script description not found")
    expect(not is_displayed(destroy_world_script_page.script_parameters_panel), "Parameters panel is shown, current script doesn't contain any parameter")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Run script")
def test_run_script(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    destroy_world_script_page.execute_script()

    expect(is_displayed(destroy_world_script_page.button_execute), "Execute button not found")
    expect(is_disabled(destroy_world_script_page.button_execute), "Execute button not disabled")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not found")
    expect(is_enabled(destroy_world_script_page.button_stop), "Stop button not enabled")

    expect(is_displayed(destroy_world_script_page.log), "Log panel not displayed")
    expect(is_displayed(destroy_world_script_page.users_input), "Input field not displayed")

    expect(is_displayed(destroy_world_script_page.add_new_tab_button), "Add new tab button not displayed")
    expect(len(destroy_world_script_page.executor_tabs) == 1, "Executor tabs amount is not 1")
    expect(is_displayed(destroy_world_script_page.active_executor_tab), "Tab is not active")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Add new tab while script running")
def test_add_new_tab(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    destroy_world_script_page.add_new_tab_button.click()

    expect(is_displayed(destroy_world_script_page.script_description), "Script description not found")
    expect(not is_displayed(destroy_world_script_page.script_parameters_panel), "Parameters panel is shown, current script doesn't contain any parameter")

    expect(is_displayed(destroy_world_script_page.button_execute), "Execute button not found")
    expect(is_enabled(destroy_world_script_page.button_execute), "Execute button not enabled")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not found")
    expect(is_disabled(destroy_world_script_page.button_stop), "Stop button not disabled")

    expect(is_displayed(destroy_world_script_page.add_new_tab_button), "Add new tab button not displayed")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Run second tab script")
def test_run_second_script(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    destroy_world_script_page.execute_script()

    expect(is_displayed(destroy_world_script_page.button_execute), "Execute button not found")
    expect(is_disabled(destroy_world_script_page.button_execute), "Execute button not disabled")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not found")
    expect(is_enabled(destroy_world_script_page.button_stop), "Stop button not enabled")

    expect(is_displayed(destroy_world_script_page.log), "Log panel not displayed")
    expect(is_displayed(destroy_world_script_page.users_input), "Input field not displayed")

    expect(len(destroy_world_script_page.executor_tabs) == 2,
           "Executor tabs amount is not 2, but {}".format(len(destroy_world_script_page.executor_tabs)))
    expect(is_displayed(destroy_world_script_page.active_executor_tab), "Tab is not active")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check text on 1st step")
def test_check_text_first_step(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    expect(destroy_world_script_page.log.get_attribute("innerHTML") == destroy_world_script_page.first_step_log_content)

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("User input while script running")
def test_user_input(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    destroy_world_script_page.users_input.send_keys("Y" + Keys.ENTER)
    time.sleep(1)

    expect(destroy_world_script_page.log.get_attribute("innerHTML") == destroy_world_script_page.first_step_log_content + destroy_world_script_page.second_step_log_content)

    expect(is_displayed(destroy_world_script_page.button_execute), "Execute button not found")
    expect(is_disabled(destroy_world_script_page.button_execute), "Execute button not disabled")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not found")
    expect(is_enabled(destroy_world_script_page.button_stop), "Stop button not enabled")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("User input to exit")
def test_user_input_no(browser, config_host):
    destroy_world_script_page = DestroyWorldScript(browser, config_host)

    destroy_world_script_page.users_input.send_keys("N" + Keys.ENTER)
    time.sleep(1)

    expect(destroy_world_script_page.log.get_attribute("innerHTML") == destroy_world_script_page.first_step_log_content + destroy_world_script_page.second_step_log_content + destroy_world_script_page.no_exit_log_content)

    expect(is_displayed(destroy_world_script_page.button_execute), "Execute button not found")
    expect(is_enabled(destroy_world_script_page.button_execute), "Execute button not enabled")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not found")
    expect(is_displayed(destroy_world_script_page.button_stop), "Stop button not disabled")

    assert_expectations()
