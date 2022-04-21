from common.pages import Page
import allure
from common.pages import is_displayed, is_enabled, is_disabled
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level


@severity(severity_level.CRITICAL)
@allure.title("Check history page is opened by click on button on home page")
def test_history_page_is_opened_on_click(browser, config_host):
    home_page = Page(browser, config_host)
    home_page.load()

    home_page.sidebar_history_button.click()

    expect(home_page.browser.current_url == config_host + "index.html#/history")

    assert_expectations()


@severity(severity_level.CRITICAL)
@allure.title("Check presented elements on history page")
def test_history_page(browser, config_host):
    home_page = Page(browser, config_host)

    expect(not is_displayed(home_page.main_app_content), "App content is found on history page")
    expect(is_displayed(home_page.history_table), "History table not found ")
    for column in home_page.history_table_column_titles:
        expect(is_displayed(home_page.find_history_column_by_name(column)), "\"{}\" not found".format(column))

    assert_expectations()
