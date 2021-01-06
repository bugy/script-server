from unittest import TestCase

from parameterized import parameterized

from tests.test_utils import mock_request_handler
from web.web_auth_utils import remove_webpack_suffixes, is_allowed_during_login


class WebpackSuffixesTest(TestCase):
    def test_remove_webpack_suffixes_when_css(self):
        normalized = remove_webpack_suffixes('js/chunk-login-vendors.59040343.css')
        self.assertEqual('js/chunk-login-vendors.css', normalized)

    def test_remove_webpack_suffixes_when_js(self):
        normalized = remove_webpack_suffixes('js/login.be16f278.js')
        self.assertEqual('js/login.js', normalized)

    def test_remove_webpack_suffixes_when_js_map(self):
        normalized = remove_webpack_suffixes('js/login.be16f278.js.map')
        self.assertEqual('js/login.js.map', normalized)

    def test_remove_webpack_suffixes_when_favicon(self):
        normalized = remove_webpack_suffixes('favicon.123.ico')
        self.assertEqual('favicon.123.ico', normalized)

    def test_remove_webpack_suffixes_when_no_suffixes(self):
        normalized = remove_webpack_suffixes('css/chunk-login-vendors.css')
        self.assertEqual('css/chunk-login-vendors.css', normalized)

    def test_remove_webpack_suffixes_when_no_extension(self):
        normalized = remove_webpack_suffixes('data/some_file')
        self.assertEqual('data/some_file', normalized)


class LoginResourcesTest(TestCase):
    @parameterized.expand([
        ('/favicon.ico'),
        ('login.html'),
        ('/js/login.be16f278.js'),
        ('/js/login.be16f278.js.map'),
        ('/js/chunk-login-vendors.18e22e7f.js'),
        ('/js/chunk-login-vendors.18e22e7f.js.map'),
        ('/img/titleBackground_login.a6c36d4c.jpg'),
        ('/css/login.8e74be0f.css'),
        ('/fonts/roboto-latin-400.60fa3c06.woff'),
        ('/fonts/roboto-latin-400.479970ff.woff2'),
        ('/fonts/roboto-latin-500.020c97dc.woff2'),
        ('/fonts/roboto-latin-500.87284894.woff')
    ])
    def test_is_allowed_during_login_when_allowed(self, resource):
        request_handler = mock_request_handler(method='GET')

        allowed = is_allowed_during_login(resource, 'login.html', request_handler)
        self.assertTrue(allowed, 'Resource ' + resource + ' should be allowed, but was not')

    def test_is_allowed_during_login_when_prohibited(self):
        request_handler = mock_request_handler(method='GET')

        resource = 'admin.html'
        allowed = is_allowed_during_login(resource, 'login.html', request_handler)
        self.assertFalse(allowed, 'Resource ' + resource + ' should NOT be allowed, but WAS')
