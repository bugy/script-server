import unittest

from ldap3 import Connection, SIMPLE, MOCK_SYNC, OFFLINE_AD_2012_R2, Server
from ldap3.utils.dn import safe_dn

from auth.auth_ldap import LdapAuthenticator
from tests import test_utils
from tests.test_utils import mock_object


class _LdapAuthenticatorMockWrapper:
    def __init__(self, username_pattern, base_dn):
        authenticator = LdapAuthenticator({
            'url': 'unused',
            'username_pattern': username_pattern,
            'base_dn': base_dn},
            test_utils.temp_folder)

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
                dn = safe_dn(dn)

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

        authenticator._connect = connect

        self.base_dn = base_dn
        self._entries = {}
        self.authenticator = authenticator

    def authenticate(self, username, password):
        return self.authenticator.authenticate(_mock_request_handler(username, password))

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


def _mock_request_handler(username, password):
    request_handler = mock_object()

    def get_argument(arg_name):
        if arg_name == 'username':
            return username
        elif arg_name == 'password':
            return password
        else:
            return None

    request_handler.get_argument = get_argument
    return request_handler
