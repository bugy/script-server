from common.pages import Page
import allure
from common.pages import is_displayed
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level

search_request = "wor"


@severity(severity_level.NORMAL)
@allure.title("Check search results")
def test_search_by_fixed_keyword_case_insensitive(browser, config_host, scripts):
    home_page = Page(browser, config_host)
    home_page.load()

    home_page.sidebar_search_button.click()
    home_page.sidebar_search_input.send_keys(search_request)

    displayed_results = home_page.all_script_links + home_page.all_groups

    for result in displayed_results:
        expect(str(result.text).find(search_request) > -1, "\"{}\" containts no search request \"{}\" but still listed after search".format(str(result.text), search_request))

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check clear search, check all scripts are back")
def test_clear_search(browser, config_host, scripts):
    home_page = Page(browser, config_host)
    home_page.sidebar_clear_search_button.click()

    for required_script in scripts:
        expect(is_displayed(home_page.get_script_link_by_name(required_script)), "Script by name \"{}\" not found after search".format(required_script))

    assert_expectations()
