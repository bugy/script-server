from common.pages import Page
import allure
from common.pages import is_displayed
from delayed_assert import expect, assert_expectations
from allure import severity, severity_level


subscripts_list = ["Ploty HTML output", "Simple HTML output"]

@severity(severity_level.NORMAL)
@allure.title("Check presented scripts group 'HTML'")
def test_presented_group_link(browser, config_host):
    home_page = Page(browser, config_host)
    home_page.load()

    group_link = home_page.get_scripts_group_by_name("HTML")
    expect(is_displayed(group_link), "Group 'HTML' link not displayed")
    expect(is_displayed(home_page.find_element("i.material-icons", group_link)), "Icon 'Show more' not displayed")

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check subscripts are hide by default")
def test_subscripts_are_hide_by_default(browser, config_host):
    home_page = Page(browser, config_host)
    home_page.load()

    for subscript in subscripts_list:
        expect(not is_displayed(home_page.get_script_link_by_name(subscript)), "Subscript {} is displayed by default".format(subscript))

    assert_expectations()


@severity(severity_level.NORMAL)
@allure.title("Check subscripts are shown after click")
def test_subscripts_are_shown_on_click(browser, config_host):
    home_page = Page(browser, config_host)
    home_page.load()

    home_page.get_scripts_group_by_name("HTML").click()

    for subscript in subscripts_list:
        expect(is_displayed(home_page.get_script_link_by_name(subscript)), "Subscript {} is not displayed after group name click".format(subscript))

    assert_expectations()
