import base64
import unittest

from utils import audit_utils


def mock_object():
    return type('', (), {})()


def mock_request_handler(ip=None, proxy_username=None, auth_username=None):
    handler_mock = mock_object()

    handler_mock.application = mock_object()
    handler_mock.application.auth = mock_object()

    handler_mock.application.auth.get_username = lambda x: auth_username

    handler_mock.request = mock_object()
    handler_mock.request.headers = {}
    if proxy_username:
        credentials = proxy_username + ':pwd'
        credentials_base64 = base64.encodebytes(credentials.encode('utf-8'))
        handler_mock.request.headers['Authorization'] = 'Basic ' + credentials_base64.decode('utf-8')

    handler_mock.request.remote_ip = ip

    return handler_mock


def get_audit_name(request_handler):
    audit_name = audit_utils.get_audit_name(request_handler)
    return normalize_hostname(audit_name)


def normalize_hostname(hostname):
    if hostname == 'ip6-localhost':
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

    def test_proxy_with_localhost(self):
        audit_name = get_audit_name(mock_request_handler(ip='127.0.0.1', proxy_username='basic_username'))
        self.assertEqual('basic_username', audit_name)

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

    def test_proxy_with_localhost(self):
        names = get_all_audit_names(mock_request_handler(ip='127.0.0.1', proxy_username='basic_username'))
        self.assertEqual({
            'hostname': 'localhost',
            'ip': '127.0.0.1',
            'proxied_username': 'basic_username'},
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
