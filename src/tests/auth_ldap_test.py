import unittest
from typing import Dict

from ldap3 import Connection, SIMPLE, MOCK_SYNC, OFFLINE_AD_2012_R2, Server
from ldap3.utils.dn import safe_dn

from auth.auth_base import AuthRejectedError, AuthFailureError
from auth.auth_ldap import LdapAuthenticator
from tests import test_utils
from tests.test_utils import mock_request_handler


class _LdapAuthenticatorMockWrapper:
    def __init__(self,
                 username_pattern=None,
                 base_dn=None,
                 search_user_by_attribute=None,
                 admin_user=None,
                 admin_password=None):
        config = {'url': 'unused'}  # type: Dict[str, object]

        if username_pattern or search_user_by_attribute:
            user_resolver_config = {}
            if username_pattern:
                user_resolver_config['username_pattern'] = username_pattern
            if search_user_by_attribute:
                user_resolver_config['search_by_attribute'] = search_user_by_attribute
            if admin_user:
                user_resolver_config['admin_user'] = admin_user
            if admin_password:
                user_resolver_config['admin_password'] = admin_password
            config['ldap_user_resolver'] = user_resolver_config

        if base_dn:
            config['base_dn'] = base_dn

        authenticator = LdapAuthenticator(config, test_utils.temp_folder)

        def connect(username, password):
            server = Server('mock_server', get_info=OFFLINE_AD_2012_R2)
            connection = Connection(
                server,
                user=username,
                password=password,
                authentication=SIMPLE,
                read_only=True,
                client_strategy=MOCK_SYNC
            )

            for dn, attrs in self._entries.items():
                dn = safe_dn(dn).lower()

                entry_added = connection.strategy.add_entry(dn, attrs)
                if not entry_added:
                    raise Exception('Failed to add entry ' + dn)

                lower_keys = {key.lower(): key for key in attrs.keys()}

                if 'samaccountname' in lower_keys:
                    account_name = attrs[lower_keys['samaccountname']][0]
                    domain_start = dn.find('dc=') + 3
                    domain_end = dn.find(',', domain_start)
                    domain = dn[domain_start:domain_end]
                    connection.server.dit[domain + '\\' + account_name] = connection.server.dit[dn]

                if 'userprincipalname' in lower_keys:
                    principal_name = attrs[lower_keys['userprincipalname']][0]
                    connection.server.dit[principal_name] = connection.server.dit[dn]

            connection.bind()
            return connection

        authenticator._ldap_connector.connect = connect

        self.base_dn = base_dn
        self._entries = {}
        self.authenticator = authenticator
        self.add_user('Admin', 'admin_pass')

    def authenticate(self, username, password):
        return self.authenticator.authenticate(_mock_request_handler(username, password))

    def perform_basic_auth(self, username, password):
        return self.authenticator.perform_basic_auth(username, password)

    def get_groups(self, username):
        return self.authenticator.get_groups(username)

    def add_user(self, cn, password, dn=None, **other_attributes):
        if dn is None:
            dn = self.to_user_dn(cn)
        self.add_entry(dn, 'person', userPassword=password, **other_attributes)

    def to_user_dn(self, cn):
        prefix = 'cn=' + cn + ',cn=Users'
        if self.base_dn:
            return prefix + ',' + self.base_dn
        return prefix

    def add_posix_user(self, cn, password, uid, **other_attributes):
        self.add_user(cn, password, uid=uid, objectClass='posixAccount', **other_attributes)

    def add_group(self, cn, member_cns=None, **other_attributes):
        if member_cns:
            member_dns = list(map(self.to_user_dn, member_cns))
        else:
            member_dns = None

        dn = 'cn=' + cn + ',cn=Groups,' + self.base_dn
        self.add_entry(dn, 'groupOfNames', member=member_dns, **other_attributes)

    def remove_group(self, cn):
        dn = 'cn=' + cn + ',cn=Groups,' + self.base_dn
        del self._entries[dn]

    def add_posix_group(self, cn, member_uids=None, **other_attributes):
        dn = 'cn=' + cn + ',cn=Groups,' + self.base_dn
        self.add_entry(dn, 'posixGroup', memberUid=member_uids, **other_attributes)

    def add_entry(self, dn, object_class, **attrs):
        if 'objectClass' in attrs:
            if not isinstance(attrs['objectClass'], list):
                attrs['objectClass'] = [attrs['objectClass']]
        else:
            attrs['objectClass'] = []
        attrs['objectClass'].append(object_class)

        self._entries[dn] = attrs


class TestFindGroups(unittest.TestCase):

    def test_load_single_group_by_member_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_user('user1', '1234')
        auth_wrapper.add_group('group1', ['user1'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_load_multiple_groups_by_member_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_user('user1', '1234')
        auth_wrapper.add_group('group1', ['user1', 'user2'])
        auth_wrapper.add_group('group2', ['user1'])
        auth_wrapper.add_group('group3', ['user3', 'user1', 'user4'])
        auth_wrapper.add_group('group4', ['user5'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1', 'group2', 'group3'], groups)

    def test_load_single_group_by_uid_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user1', '1234', 'uid_X')
        auth_wrapper.add_posix_group('group1', ['uid_X'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1'], groups)

    def test_load_multiple_groups_by_uid_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user1', '1234', 'uid_X')
        auth_wrapper.add_posix_group('group1', ['uid_X'])
        auth_wrapper.add_posix_group('group2', ['uid_X'])
        auth_wrapper.add_posix_group('group3', ['uid_X'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1', 'group2', 'group3'], groups)

    def test_load_multiple_groups_by_uid_when_not_all_match(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user1', '1234', 'uid_X')
        auth_wrapper.add_posix_group('group1', ['uid_X'])
        auth_wrapper.add_posix_group('group2', ['uid_123'])
        auth_wrapper.add_posix_group('group3', ['uid_X'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1', 'group3'], groups)

    def test_load_single_group_by_uid_when_dn_has_parenthesss(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user (1)', '1234', 'uid (X)')
        auth_wrapper.add_posix_group('group1', ['uid (X)'])

        groups = self.auth_and_get_groups('user (1)', auth_wrapper)
        self.assertCountEqual(['group1'], groups)

    def test_load_multiple_groups_by_member_and_uid_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user1', '1234', 'uid_X')
        auth_wrapper.add_posix_group('group1', ['uid_X'])
        auth_wrapper.add_group('group2', ['user1'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1', 'group2'], groups)

    def test_load_same_groups_by_member_and_uid_when_dn_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=ldap,dc=test', 'dc=ldap,dc=test')
        auth_wrapper.add_posix_user('user1', '1234', 'uid_X')
        auth_wrapper.add_group('group1', ['user1', 'user2'], memberUid=['uid_X'], objectClass='posixGroup')
        auth_wrapper.add_group('group2', ['user1'], memberUid=['uid_X', 'uid_Y'], objectClass='posixGroup')

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertCountEqual(['group1', 'group2'], groups)

    def test_load_single_group_by_member_when_sam_account_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('some_domain\\$username', 'dc=some_domain,dc=test')
        auth_wrapper.add_user('User Noname', '1234', sAMAccountName='user1')
        auth_wrapper.add_group('group1', ['User Noname'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_load_single_group_by_member_when_sam_account_template_with_parentheses(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('some_domain\\$username', 'dc=some_domain,dc=test')
        auth_wrapper.add_user('User (Noname)', '1234', sAMAccountName='user (1)')
        auth_wrapper.add_group('group1', ['User (Noname)'])

        groups = self.auth_and_get_groups('user (1)', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_load_single_group_by_uid_when_sam_account_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('some_domain\\$username', 'dc=some_domain,dc=test')
        auth_wrapper.add_posix_user('User Noname', '1234', 'uid_X', sAMAccountName='user1')
        auth_wrapper.add_posix_group('group1', ['uid_X'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_load_single_group_by_member_when_user_principal_template(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('$username@buggy.net', 'dc=buggy,dc=net')
        auth_wrapper.add_user('User Noname', '1234', userPrincipalName='user1@buggy.net')
        auth_wrapper.add_group('group1', ['User Noname'])

        groups = self.auth_and_get_groups('user1', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_load_single_group_by_member_when_user_principal_template_with_parentheses(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('$username@buggy.net', 'dc=buggy,dc=net')
        auth_wrapper.add_user('User (Noname)', '1234', userPrincipalName='user (1)@buggy.net')
        auth_wrapper.add_group('group1', ['User (Noname)'])

        groups = self.auth_and_get_groups('user (1)', auth_wrapper)
        self.assertEqual(['group1'], groups)

    def test_cannot_load_group_when_same_principal_names(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper('$username@buggy.net', 'dc=buggy,dc=net')
        auth_wrapper.add_user('user1', '1234', userPrincipalName='userX@buggy.net')
        auth_wrapper.add_user('user2', '1234', userPrincipalName='userX@buggy.net')
        auth_wrapper.add_group('group1', ['user1', 'user2'])

        groups = self.auth_and_get_groups('userX', auth_wrapper)
        self.assertEqual([], groups)

    def auth_and_get_groups(self, username, auth_wrapper):
        self.authenticate(username, '1234', auth_wrapper)
        groups = auth_wrapper.get_groups(username)
        return groups

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

    def authenticate(self, username, password, auth_wrapper):
        user = auth_wrapper.authenticate(username, password)
        self.assertEqual(user, username)


class TestGroupsPersistence(unittest.TestCase):
    def test_get_groups_after_login(self):
        self.auth_wrapper.add_user('user1', '1234')
        self.auth_wrapper.add_group('group1', ['user1'])

        self.authenticate('user1', '1234')
        groups = self.auth_wrapper.get_groups('user1')
        self.assertCountEqual(['group1'], groups)

    def test_get_groups_after_login_for_different_users(self):
        self.auth_wrapper.add_user('user1', '1234')
        self.auth_wrapper.add_user('user2', '1234')
        self.auth_wrapper.add_group('group1', ['user1'])
        self.auth_wrapper.add_group('group2', ['user2'])

        self.authenticate('user1', '1234')
        groups = self.auth_wrapper.get_groups('user1')
        self.assertCountEqual(['group1'], groups)

        self.authenticate('user2', '1234')
        groups = self.auth_wrapper.get_groups('user2')
        self.assertCountEqual(['group2'], groups)

    def test_renew_groups_after_login(self):
        self.auth_wrapper.add_user('user1', '1234')
        self.auth_wrapper.add_group('group1', ['user1'])

        self.authenticate('user1', '1234')

        self.auth_wrapper.remove_group('group1')
        self.auth_wrapper.add_group('group2', ['user1'])
        self.auth_wrapper.add_group('group3', ['user1'])

        self.authenticate('user1', '1234')
        groups = self.auth_wrapper.get_groups('user1')
        self.assertCountEqual(['group2', 'group3'], groups)

    def test_restore_groups_after_restart(self):
        self.auth_wrapper.add_user('user1', '1234')
        self.auth_wrapper.add_group('group1', ['user1'])

        self.authenticate('user1', '1234')

        new_wrapper = self.create_wrapper()

        groups = new_wrapper.get_groups('user1')
        self.assertCountEqual(['group1'], groups)

    def setUp(self):
        test_utils.setup()

        self.auth_wrapper = self.create_wrapper()

    def create_wrapper(self):
        return _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=buggy,dc=net', 'dc=buggy,dc=net')

    def tearDown(self):
        test_utils.cleanup()

    def authenticate(self, username, password):
        user = self.auth_wrapper.authenticate(username, password)
        self.assertEqual(user, username)


class TestAuthenticate(unittest.TestCase):

    def test_perform_basic_auth_success(self):
        authenticated = self.auth_wrapper.perform_basic_auth('user1', '1234')
        self.assertEqual(True, authenticated)
        self.assertEqual(['group1'], self.auth_wrapper.get_groups('user1'))

    def test_perform_basic_auth_failure(self):
        self.assertRaisesRegex(
            AuthRejectedError,
            'Invalid credentials',
            self.auth_wrapper.perform_basic_auth,
            'user1',
            '555')

    def setUp(self):
        test_utils.setup()

        self.auth_wrapper = self.create_wrapper()

        self.auth_wrapper.add_user('user1', '1234')
        self.auth_wrapper.add_group('group1', ['user1'])

    def create_wrapper(self):
        return _LdapAuthenticatorMockWrapper('cn=$username,cn=Users,dc=buggy,dc=net', 'dc=buggy,dc=net')

    def tearDown(self):
        test_utils.cleanup()


class TestLdapUserResolver(unittest.TestCase):

    def test_authenticate_with_uid_resolver(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='uid',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='admin_pass'
        )

        auth_wrapper.add_user('John Doe', 'user_pass', uid='johndoe')

        user = auth_wrapper.authenticate('johndoe', 'user_pass')
        self.assertEqual(user, 'johndoe')

    def test_authenticate_with_different_attribute(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='sAMAccountName',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='admin_pass'
        )

        auth_wrapper.add_user('Jane Smith', 'user_pass', sAMAccountName='jsmith')

        user = auth_wrapper.authenticate('jsmith', 'user_pass')
        self.assertEqual(user, 'jsmith')

    def test_authenticate_fails_with_wrong_uid(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='uid',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='admin_pass'
        )

        auth_wrapper.add_user('John Doe', 'user_pass', uid='johndoe')

        self.assertRaisesRegex(
            AuthRejectedError,
            'Invalid credentials',
            auth_wrapper.authenticate,
            'nonexistent',
            'user_pass'
        )

    def test_authenticate_fails_with_wrong_password(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='uid',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='admin_pass'
        )

        auth_wrapper.add_user('John Doe', 'user_pass', uid='johndoe')

        self.assertRaisesRegex(
            AuthRejectedError,
            'Invalid credentials',
            auth_wrapper.authenticate,
            'johndoe',
            'wrong_pass'
        )

    def test_authenticate_fails_with_wrong_admin_password(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='uid',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='wrong_pass'
        )

        auth_wrapper.add_user('John Doe', 'user_pass', uid='johndoe')

        self.assertRaisesRegex(
            AuthFailureError,
            'Failed to bind with admin LDAP user: invalidCredentials',
            auth_wrapper.authenticate,
            'johndoe',
            'user_pass'
        )

    def test_load_groups_with_uid_resolver(self):
        auth_wrapper = _LdapAuthenticatorMockWrapper(
            base_dn='dc=ldap,dc=test',
            search_user_by_attribute='uid',
            admin_user='cn=admin,cn=users,dc=ldap,dc=test',
            admin_password='admin_pass'
        )

        auth_wrapper.add_user('John Doe', 'user_pass', uid='johndoe')
        auth_wrapper.add_group('admin_group', ['John Doe'])

        user = auth_wrapper.authenticate('johndoe', 'user_pass')
        groups = auth_wrapper.get_groups('johndoe')
        self.assertEqual(['admin_group'], groups)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestConfigValidation(unittest.TestCase):

    def test_reject_both_username_pattern_and_search_by_attribute(self):
        config = {
            'url': 'ldap://localhost',
            'ldap_user_resolver': {
                'username_pattern': 'cn=$username,dc=test',
                'search_by_attribute': 'uid',
                'admin_user': 'admin',
                'admin_password': 'pass'
            }
        }

        with self.assertRaisesRegex(ValueError, 'Cannot specify both username_pattern and search_by_attribute'):
            LdapAuthenticator(config, test_utils.temp_folder)

    def test_reject_neither_username_pattern_nor_search_by_attribute(self):
        config = {
            'url': 'ldap://localhost',
            'ldap_user_resolver': {
                'admin_user': 'admin'
            }
        }

        with self.assertRaisesRegex(ValueError, 'Either username_pattern or search_by_attribute must be specified'):
            LdapAuthenticator(config, test_utils.temp_folder)

    def test_reject_incomplete_search_by_attribute_config(self):
        config = {
            'url': 'ldap://localhost',
            'ldap_user_resolver': {
                'search_by_attribute': 'uid',
                'admin_user': 'admin'
                # Missing admin_password
            }
        }

        with self.assertRaisesRegex(Exception, 'admin_password.*for ldap_user_resolver'):
            LdapAuthenticator(config, test_utils.temp_folder)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


def _mock_request_handler(username, password):
    return mock_request_handler(arguments={'username': username, 'password': password})
