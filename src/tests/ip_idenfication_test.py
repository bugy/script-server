import unittest

from auth.identification import IpBasedIdentification
from auth.tornado_auth import TornadoAuth
from tests.test_utils import mock_object
from utils import date_utils

COOKIE_KEY = 'client_id_token'


def mock_request_handler(ip=None, x_forwarded_for=None, x_real_ip=None, saved_token=None):
    handler_mock = mock_object()

    handler_mock.application = mock_object()
    handler_mock.application.auth = TornadoAuth(None)

    handler_mock.request = mock_object()
    handler_mock.request.headers = {}

    handler_mock.request.remote_ip = ip

    if x_forwarded_for:
        handler_mock.request.headers['X-Forwarded-For'] = x_forwarded_for

    if x_real_ip:
        handler_mock.request.headers['X-Real-IP'] = x_real_ip

    cookies = {COOKIE_KEY: saved_token}

    def get_secure_cookie(name):
        values = cookies[name]
        if values is not None:
            return values.encode('utf8')
        return None

    def set_secure_cookie(key, value, expires_days=30):
        cookies[key] = value

    def clear_cookie(key):
        if cookies[key] is not None:
            cookies[key] = None

    handler_mock.get_cookie = lambda key: cookies[key]
    handler_mock.get_secure_cookie = get_secure_cookie
    handler_mock.set_secure_cookie = set_secure_cookie
    handler_mock.clear_cookie = clear_cookie

    return handler_mock


class IpIdentificationTest(unittest.TestCase):

    def test_localhost_ip_trusted_identification(self):
        identification = IpBasedIdentification(['127.0.0.1'])
        id = identification.identify(mock_request_handler(ip='127.0.0.1'))
        self.assertEqual('127.0.0.1', id)

    def test_some_ip_trusted_identification(self):
        identification = IpBasedIdentification(['192.168.21.13'])
        id = identification.identify(mock_request_handler(ip='192.168.21.13'))
        self.assertEqual('192.168.21.13', id)

    def test_ip_untrusted_identification(self):
        identification = IpBasedIdentification([])
        id = identification.identify(mock_request_handler(ip='192.168.21.13'))
        self.assertNotEqual('192.168.21.13', id)

    def test_ip_untrusted_identification_for_different_connections(self):
        identification = IpBasedIdentification([])

        ids = set()
        for _ in range(0, 100):
            ids.add(identification.identify(mock_request_handler(ip='192.168.21.13')))

        self.assertEqual(100, len(ids))

    def test_ip_untrusted_identification_same_connection(self):
        identification = IpBasedIdentification([])

        request_handler = mock_request_handler(ip='192.168.21.13')
        id1 = identification.identify(request_handler)
        id2 = identification.identify(request_handler)
        self.assertEqual(id1, id2)

    def test_proxied_ip_behind_trusted(self):
        identification = IpBasedIdentification(['127.0.0.1'])

        request_handler = mock_request_handler(ip='127.0.0.1', x_forwarded_for='192.168.21.13')
        id = identification.identify(request_handler)
        self.assertEqual('192.168.21.13', id)

    def test_proxied_ip_behind_untrusted(self):
        identification = IpBasedIdentification([])

        request_handler = mock_request_handler(ip='127.0.0.1', x_forwarded_for='192.168.21.13')
        id = identification.identify(request_handler)
        self.assertNotEqual('192.168.21.13', id)
        self.assertNotEqual('127.0.0.1', id)

    def test_change_to_trusted(self):
        request_handler = mock_request_handler(ip='192.168.21.13')

        old_id = IpBasedIdentification([]).identify(request_handler)

        trusted_identification = IpBasedIdentification(['192.168.21.13'])
        new_id = trusted_identification.identify(request_handler)

        self.assertNotEqual(old_id, new_id)
        self.assertEqual(new_id, '192.168.21.13')
        self.assertIsNone(request_handler.get_cookie(COOKIE_KEY))

    def test_change_to_untrusted(self):
        request_handler = mock_request_handler(ip='192.168.21.13')

        trusted_identification = IpBasedIdentification(['192.168.21.13'])
        old_id = trusted_identification.identify(request_handler)

        new_id = IpBasedIdentification([]).identify(request_handler)

        self.assertNotEqual(old_id, new_id)
        self.assertNotEqual(new_id, '192.168.21.13')
        self.assertIsNotNone(request_handler.get_cookie(COOKIE_KEY))

    def test_no_cookie_change_for_same_user(self):
        request_handler = mock_request_handler(ip='192.168.21.13')

        identification = IpBasedIdentification([])

        identification.identify(request_handler)
        cookie1 = request_handler.get_cookie(COOKIE_KEY)
        identification.identify(request_handler)
        cookie2 = request_handler.get_cookie(COOKIE_KEY)

        self.assertEqual(cookie1, cookie2)

    def test_refresh_old_cookie_with_same_id(self):
        request_handler = mock_request_handler(ip='192.168.21.13')

        identification = IpBasedIdentification([])

        id = '1234567'
        token_expiry = str(date_utils.get_current_millis() + date_utils.days_to_ms(2))
        old_token = id + '&' + token_expiry
        request_handler.set_secure_cookie(COOKIE_KEY, old_token)

        new_id = identification.identify(request_handler)
        new_token = request_handler.get_cookie(COOKIE_KEY)

        self.assertEqual(new_id, id)
        self.assertNotEqual(old_token, new_token)

    def test_broken_token_structure(self):
        request_handler = mock_request_handler(ip='192.168.21.13')
        request_handler.set_secure_cookie(COOKIE_KEY, 'something')

        IpBasedIdentification([]).identify(request_handler)

        new_token = request_handler.get_cookie(COOKIE_KEY)

        self.assertNotEqual(new_token, 'something')

    def test_broken_token_timestamp(self):
        request_handler = mock_request_handler(ip='192.168.21.13')
        request_handler.set_secure_cookie(COOKIE_KEY, 'something&hello')

        id = IpBasedIdentification([]).identify(request_handler)

        new_token = request_handler.get_cookie(COOKIE_KEY)

        self.assertNotEqual('something', id)
        self.assertNotEqual(new_token, 'something&hello')

    def test_old_token_timestamp(self):
        request_handler = mock_request_handler(ip='192.168.21.13')
        request_handler.set_secure_cookie(COOKIE_KEY, 'something&100000')

        id = IpBasedIdentification([]).identify(request_handler)

        new_token = request_handler.get_cookie(COOKIE_KEY)

        self.assertNotEqual('something', id)
        self.assertNotEqual(new_token, 'something&100000')
