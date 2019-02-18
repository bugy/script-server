import sys
import unittest
from unittest import mock

from tornado import httpclient
from tornado.httpclient import AsyncHTTPClient
from tornado.util import Configurable

from tests import test_utils
from web.client import tornado_client_config


class TestInitializeClient(unittest.TestCase):
    def test_no_proxy(self):
        self.run_initialize()

        self.assert_proxy(None, None)

    def test_https_proxy_lowercase(self):
        test_utils.set_env_value('https_proxy', 'https://my.proxy.com:8080/path')
        self.run_initialize()

        self.assert_proxy('my.proxy.com', 8080)

    def test_http_proxy_uppercase(self):
        test_utils.set_env_value('HTTP_PROXY', 'http://localhost:12345')
        self.run_initialize()

        self.assert_proxy('localhost', 12345)

    def test_proxy_credentials(self):
        test_utils.set_env_value('HTTP_PROXY', 'http://user999:qwerty@localhost:12345')
        self.run_initialize()

        self.assert_proxy('localhost', 12345, username='user999', password='qwerty')

    def test_default_port(self):
        test_utils.set_env_value('HTTP_PROXY', 'http://192.168.1.1')
        self.run_initialize()

        self.assert_proxy('192.168.1.1', 3128)

    def test_no_pycurl(self):
        test_utils.set_env_value('HTTP_PROXY', 'http://192.168.1.1')
        with mock.patch.dict(sys.modules, {'pycurl': None}):
            tornado_client_config.initialize()

        self.assert_proxy(None, None)

    def run_initialize(self):
        with mock.patch.dict(sys.modules, {'pycurl': sys}):
            tornado_client_config.initialize()

    def assert_proxy(self, host, port, username=None, password=None):
        kwargs = AsyncHTTPClient.configurable_base()._Configurable__impl_kwargs
        defaults = kwargs['defaults'] if kwargs else {}

        self.assertEqual(host, defaults.get('proxy_host'))
        self.assertEqual(port, defaults.get('proxy_port'))
        self.assertEqual(username, defaults.get('proxy_username'))
        self.assertEqual(password, defaults.get('proxy_password'))

    def setUp(self):
        super().setUp()
        test_utils.setup()

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

        httpclient.AsyncHTTPClient.configure(None)
