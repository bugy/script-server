from common.pages import Page
import allure
from common.pages import is_displayed, is_enabled, is_disabled
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level


@severity(severity_level.CRITICAL)
@allure.title("Check presented elements on main page")
def test_home_page(browser, config_host):
    home_page = Page(browser, config_host)
    home_page.load()

    expect(is_displayed(home_page.sidebar), "Sidebar not found")
    expect(is_displayed(home_page.sidebar_header), "Header on sidebar not found")
    expect(is_displayed(home_page.sidebar_history_button), "History button on sidebar not found")
    expect(is_displayed(home_page.sidebar_scripts_list), "Scripts list not found")
    expect(is_displayed(home_page.sidebar_search_button), "Search button not found")
    expect(is_displayed(home_page.sidebar_header_link), "Header link not found")
    expect(not is_displayed(home_page.main_app_content), "App content is displayed")

    assert_expectations()


@severity(severity_level.CRITICAL)
@allure.title("Check appeared app content on random script click")
def test_app_content(browser, config_host):
    home_page = Page(browser, config_host)

    for script_link in home_page.all_script_links:
        script_link.click()

        expect(is_displayed(home_page.sidebar), "Sidebar not found")
        expect(is_displayed(home_page.sidebar_header), "Header on sidebar not found")
        expect(is_displayed(home_page.sidebar_history_button), "History button on sidebar not found")
        expect(is_displayed(home_page.sidebar_scripts_list), "Scripts list not found")
        expect(is_displayed(home_page.sidebar_search_button), "Search button not found")
        expect(is_displayed(home_page.sidebar_header_link), "Header link not found")

        expect(is_displayed(home_page.main_app_content), "App content not found")
        expect(is_displayed(home_page.script_header), "Script header not found")
        expect(is_displayed(home_page.actions_panel), "Action panel not found")
        expect(is_displayed(home_page.button_execute), "Execute button not found")
        expect(is_enabled(home_page.button_execute), "Execute button not enabled")
        expect(is_displayed(home_page.button_stop), "Stop button not found")
        expect(is_disabled(home_page.button_stop), "Stop button not disabled")

        expect(not is_displayed(home_page.log), "Log panel is displayed before script run")
        expect(not is_displayed(home_page.users_input), "Input field is displayed before script run")

    assert_expectations()


