import base64
import unittest

from tests.test_utils import mock_object
from utils import audit_utils, os_utils
from utils.audit_utils import get_audit_username


def mock_request_handler(ip=None, proxy_username=None, auth_username=None, proxied_ip=None):
    handler_mock = mock_object()

    handler_mock.application = mock_object()

    handler_mock.application.identification = mock_object()
    handler_mock.application.identification.identify_for_audit = lambda x: auth_username

    handler_mock.request = mock_object()
    handler_mock.request.headers = {}
    if proxy_username:
        credentials = proxy_username + ':pwd'
        credentials_base64 = base64.encodebytes(credentials.encode('utf-8'))
        handler_mock.request.headers['Authorization'] = 'Basic ' + credentials_base64.decode('utf-8')

    handler_mock.request.remote_ip = ip

    if proxied_ip:
        handler_mock.request.headers['X-Forwarded-For'] = proxied_ip

    return handler_mock


def get_audit_name(request_handler):
    audit_name = audit_utils.get_audit_name_from_request(request_handler)
    return normalize_hostname(audit_name)


def normalize_hostname(hostname):
    if hostname == 'ip6-localhost':
        return 'localhost'
    if os_utils.is_win():
        import platform
        if hostname == platform.node():
            return 'localhost'

    return hostname


def get_all_audit_names(request_handler):
    names = audit_utils.get_all_audit_names(request_handler)
    if 'hostname' in names:
        names['hostname'] = normalize_hostname(names['hostname'])

    return names


class TestGetAuditName(unittest.TestCase):
    def test_localhost_ip_only(self):
        audit_name = get_audit_name(mock_request_handler(ip='127.0.0.1'))
        self.assertEqual('localhost', audit_name)

    def test_unknown_ip_only(self):
        audit_name = get_audit_name(mock_request_handler(ip='128.5.3.2'))
        self.assertEqual('128.5.3.2', audit_name)

    def test_auth_with_localhost(self):
        audit_name = get_audit_name(mock_request_handler(ip='127.0.0.1', auth_username='ldap_user'))
        self.assertEqual('ldap_user', audit_name)

    def test_proxied_name_with_localhost(self):
        audit_name = get_audit_name(mock_request_handler(ip='127.0.0.1', proxy_username='basic_username'))
        self.assertEqual('basic_username', audit_name)

    def test_proxied_ip_only(self):
        audit_name = get_audit_name(mock_request_handler(ip='127.0.0.1', proxied_ip='128.5.3.2'))
        self.assertEqual('128.5.3.2', audit_name)

    def test_proxied_hostname(self):
        audit_name = get_audit_name(mock_request_handler(ip='128.5.3.2', proxied_ip='127.0.0.1'))
        self.assertEqual('localhost', audit_name)

    def test_full_audit_localhost(self):
        audit_name = get_audit_name(mock_request_handler(
            ip='127.0.0.1',
            auth_username='ldap_user',
            proxy_username='basic_username'))
        self.assertEqual('ldap_user', audit_name)


class TestGetAllAuditNames(unittest.TestCase):
    def test_localhost_ip_only(self):
        names = get_all_audit_names(mock_request_handler(ip='127.0.0.1'))
        self.assertEqual({'hostname': 'localhost', 'ip': '127.0.0.1'}, names)

    def test_unknown_ip_only(self):
        names = get_all_audit_names(mock_request_handler(ip='128.5.3.2'))
        self.assertEqual({'ip': '128.5.3.2'}, names)

    def test_auth_with_localhost(self):
        names = get_all_audit_names(mock_request_handler(ip='127.0.0.1', auth_username='ldap_user'))
        self.assertEqual({
            'hostname': 'localhost',
            'ip': '127.0.0.1',
            'auth_username': 'ldap_user'},
            names)

    def test_proxied_name_with_localhost(self):
        names = get_all_audit_names(mock_request_handler(ip='127.0.0.1', proxy_username='basic_username'))
        self.assertEqual({
            'hostname': 'localhost',
            'ip': '127.0.0.1',
            'proxied_username': 'basic_username'},
            names)

    def test_proxied_ip(self):
        names = get_all_audit_names(mock_request_handler(ip='127.0.0.1', proxied_ip='128.5.3.2'))
        self.assertEqual({
            'hostname': 'localhost',
            'ip': '127.0.0.1',
            'proxied_ip': '128.5.3.2'},
            names)

    def test_full_audit_localhost(self):
        names = get_all_audit_names(mock_request_handler(
            ip='127.0.0.1',
            auth_username='ldap_user',
            proxy_username='basic_username'))
        self.assertEqual({
            'hostname': 'localhost',
            'ip': '127.0.0.1',
            'auth_username': 'ldap_user',
            'proxied_username': 'basic_username'},
            names)


class TestGetAuditUsername(unittest.TestCase):
    def test_auth_username(self):
        username = get_audit_username({'auth_username': 'user_X', 'ip': '123'})
        self.assertEqual('user_X', username)

    def test_proxied_username(self):
        username = get_audit_username({'proxied_username': 'Its me', 'hostname': '123'})
        self.assertEqual('Its me', username)

    def test_no_username(self):
        username = get_audit_username({
            'proxied_hostname': 'my host',
            'hostname': 'localhost',
            'ip': '123.456',
            'proxied_ip': '987'})
        self.assertIsNone(username)

    def test_auth_username_and_proxied_username(self):
        username = get_audit_username({'proxied_username': 'Its me', 'auth_username': 'user_X'})
        self.assertEqual('user_X', username)

