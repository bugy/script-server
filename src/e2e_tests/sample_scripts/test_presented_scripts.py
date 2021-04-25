from common.pages import Page
import allure
from common.pages import is_displayed
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level


@severity(severity_level.NORMAL)
@allure.title("Check presented scripts by names")
def test_presented_scripts_by_name(browser, config_host, scripts):
    home_page = Page(browser, config_host)
    home_page.load()

    for required_script in scripts:
        expect(is_displayed(home_page.get_script_link_by_name(required_script)), "Script by name \"{}\" not found".format(required_script))

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check scripts amount")
def test_presented_scripts_amount(browser, config_host, scripts):
    home_page = Page(browser, config_host)

    assert len(scripts) == len(home_page.all_script_links)
