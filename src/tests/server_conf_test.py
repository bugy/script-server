import json
import os
import unittest

from parameterized import parameterized

from auth.auth_gitlab import GitlabOAuthAuthenticator
from auth.auth_google_oauth import GoogleOauthAuthenticator
from auth.auth_htpasswd import HtpasswdAuthenticator
from auth.auth_ldap import LdapAuthenticator
from auth.authorization import ANY_USER
from communications.alerts_service import AlertsService
from features.executions_callback_feature import ExecutionsCallbackFeature
from model import server_conf
from model.model_helper import InvalidValueException
from model.server_conf import _prepare_allowed_users
from tests import test_utils
from utils import file_utils, custom_json


class TestPrepareAllowedUsers(unittest.TestCase):
    def test_keep_allowed_users_without_admins_and_groups(self):
        allowed_users = _prepare_allowed_users(['user1', 'user2'], None, None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_coerce_none_users_to_any(self):
        allowed_users = _prepare_allowed_users(None, None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users('*', None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_list_with_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users(['user1', '*', 'user2'], None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_list_with_untrimmed_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users(['user1', '\t*  ', 'user2'], None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_untrimmed_values(self):
        allowed_users = _prepare_allowed_users([' user1 ', ' ', '\tuser2\t'], None, None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_admin_users(self):
        allowed_users = _prepare_allowed_users(['user1'], ['user2'], None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_admin_users_with_same(self):
        allowed_users = _prepare_allowed_users(['user1', 'user2'], ['user2', 'user3'], None)
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_users_from_1_group(self):
        allowed_users = _prepare_allowed_users(['user1'], None, {'group1': ['user2']})
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_group_users_from_2_groups(self):
        allowed_users = _prepare_allowed_users(['user1'], None, {'group1': ['user2'], 'group2': ['user3']})
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_users_from_2_groups_when_same(self):
        allowed_users = _prepare_allowed_users(
            ['user1', 'user2'], None,
            {'group1': ['user2', 'user3'], 'group2': ['user4', 'user3']})
        self.assertCountEqual(['user1', 'user2', 'user3', 'user4'], allowed_users)

    def test_add_group_and_admin_users(self):
        allowed_users = _prepare_allowed_users(
            ['user1'], ['user2'], {'group1': ['user3']})
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_and_admin_users_when_same(self):
        allowed_users = _prepare_allowed_users(
            ['user1', 'user2', 'user3'],
            ['user2', 'userX'],
            {'group1': ['userY', 'user3']})
        self.assertCountEqual(['user1', 'user2', 'user3', 'userX', 'userY'], allowed_users)


class TestAdminUsersInit(unittest.TestCase):
    def test_single_list(self):
        config = _from_json({'access': {'admin_users': ['userX']}})
        self.assertEqual(['userX'], config.admin_users)

    def test_single_string(self):
        config = _from_json({'access': {'admin_users': 'abc'}})
        self.assertEqual(['abc'], config.admin_users)

    def test_missing_when_no_access_section(self):
        config = _from_json({})
        self.assertEqual(['127.0.0.1', '::1'], config.admin_users)

    def test_missing_when_access_exist_without_admin_users(self):
        config = _from_json({'access': {'allowed_users': ['user1', 'user2']}})
        self.assertEqual(['127.0.0.1', '::1'], config.admin_users)

    def test_missing_when_access_exist_without_admin_users_and_auth_enabled(self):
        config = _from_json({'access': {'allowed_users': ['user1', 'user2']},
                             'auth': {'type': 'ldap', 'url': 'localhost'}})
        self.assertEqual([], config.admin_users)

    def test_list_with_multiple_values(self):
        config = _from_json({'access': {'admin_users': ['user1', 'user2', 'user3']}})
        self.assertCountEqual(['user1', 'user2', 'user3'], config.admin_users)

    def test_list_with_any_user(self):
        config = _from_json({'access': {'admin_users': ['user1', '*', 'user3']}})
        self.assertEqual([ANY_USER], config.admin_users)

    def test_list_any_user_single_string(self):
        config = _from_json({'access': {'admin_users': '*'}})
        self.assertCountEqual([ANY_USER], config.admin_users)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestFullHistoryUsersInit(unittest.TestCase):
    def test_single_list(self):
        config = _from_json({'access': {'full_history': ['userX']}})
        self.assertEqual(['userX'], config.full_history_users)

    def test_single_string(self):
        config = _from_json({'access': {'full_history': 'abc'}})
        self.assertEqual(['abc'], config.full_history_users)

    def test_missing_when_no_access_section(self):
        config = _from_json({})
        self.assertEqual([], config.full_history_users)

    def test_missing_when_access_exist_without_full_history(self):
        config = _from_json({'access': {'allowed_users': ['user1', 'user2']}})
        self.assertEqual([], config.full_history_users)

    def test_list_with_multiple_values(self):
        config = _from_json({'access': {'full_history': ['user1', 'user2', 'user3']}})
        self.assertCountEqual(['user1', 'user2', 'user3'], config.full_history_users)

    def test_list_with_any_user(self):
        config = _from_json({'access': {'full_history': ['user1', '*', 'user3']}})
        self.assertEqual([ANY_USER], config.full_history_users)

    def test_list_any_user_single_string(self):
        config = _from_json({'access': {'full_history': '*'}})
        self.assertCountEqual([ANY_USER], config.full_history_users)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestCodeEditorUsersInit(unittest.TestCase):
    def test_single_list(self):
        config = _from_json({'access': {'code_editors': ['userX']}})
        self.assertEqual(['userX'], config.code_editor_users)

    def test_single_string(self):
        config = _from_json({'access': {'code_editors': 'abc'}})
        self.assertEqual(['abc'], config.code_editor_users)

    def test_missing_when_no_access_section(self):
        config = _from_json({})
        self.assertEqual(config.admin_users, config.code_editor_users)

    def test_missing_when_access_exist_without_code_editor_users(self):
        config = _from_json({'access': {'allowed_users': ['user1', 'user2']}})
        self.assertEqual(config.admin_users, config.code_editor_users)

    def test_list_with_multiple_values(self):
        config = _from_json({'access': {'code_editors': ['user1', 'user2', 'user3']}})
        self.assertCountEqual(['user1', 'user2', 'user3'], config.code_editor_users)

    def test_list_with_any_user(self):
        config = _from_json({'access': {'code_editors': ['user1', '*', 'user3']}})
        self.assertEqual([ANY_USER], config.code_editor_users)

    def test_list_any_user_single_string(self):
        config = _from_json({'access': {'code_editors': '*'}})
        self.assertCountEqual([ANY_USER], config.code_editor_users)

    def test_default_users_with_admin_section(self):
        config = _from_json({'access': {'admin_users': ['admin_user', '@some_group']}})
        self.assertCountEqual(config.admin_users, config.code_editor_users)

    def test_users_with_admin_section(self):
        config = _from_json({'access': {'admin_users': ['admin_user', '@some_group'],
                                        'code_editors': ['another_user']}})
        self.assertCountEqual(['another_user'], config.code_editor_users)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestMaxRequestSize(unittest.TestCase):
    def test_int_value(self):
        config = _from_json({'max_request_size': 5})
        self.assertEqual(5, config.max_request_size_mb)

    def test_string_value(self):
        config = _from_json({'max_request_size': '123'})
        self.assertEqual(123, config.max_request_size_mb)

    def test_default_value(self):
        config = _from_json({})
        self.assertEqual(10, config.max_request_size_mb)


class TestSimpleConfigs(unittest.TestCase):
    def test_server_title(self):
        config = _from_json({'title': 'my server'})
        self.assertEqual('my server', config.title)

    def test_server_title_default(self):
        config = _from_json({})
        self.assertIsNone(config.title)

    def test_enable_script_titles_enabled(self):
        config = _from_json({'enable_script_titles': 'true'})
        self.assertIs(True, config.enable_script_titles)

    def test_enable_script_titles_disabled(self):
        config = _from_json({'enable_script_titles': 'false'})
        self.assertIs(False, config.enable_script_titles)

    def test_enable_script_titles_default(self):
        config = _from_json({})
        self.assertIs(True, config.enable_script_titles)

    def test_comments_json(self):
        config = _from_json(
            custom_json.loads("""
                    {
                        // "title": "my server"
                        "title": "my server2"
                    }""")
        )
        self.assertEqual('my server2', config.title)


class TestAuthConfig(unittest.TestCase):
    def test_google_oauth(self):
        config = _from_json({'auth': {'type': 'google_oauth',
                                      'client_id': '1234',
                                      'secret': 'abcd'},
                             'access': {
                                 'allowed_users': []
                             }})
        self.assertIsInstance(config.authenticator, GoogleOauthAuthenticator)
        self.assertEquals('1234', config.authenticator.client_id)
        self.assertEquals('abcd', config.authenticator.secret)

    def test_google_oauth_without_allowed_users(self):
        with self.assertRaisesRegex(Exception, 'access.allowed_users field is mandatory for google_oauth'):
            _from_json({'auth': {'type': 'google_oauth',
                                 'client_id': '1234',
                                 'secret': 'abcd'}})

    def test_gitlab_oauth(self):
        config = _from_json({
            'auth': {
                'type': 'gitlab',
                'client_id': '1234',
                'secret': 'abcd',
            },
            'access': {
                'allowed_users': []
            }})

        self.assertIsInstance(config.authenticator, GitlabOAuthAuthenticator)

    def test_ldap(self):
        config = _from_json({'auth': {'type': 'ldap',
                                      'url': 'http://test-ldap.net',
                                      'username_pattern': '|$username|',
                                      'base_dn': 'dc=test',
                                      'version': 3}})
        self.assertIsInstance(config.authenticator, LdapAuthenticator)
        self.assertEquals('http://test-ldap.net', config.authenticator.url)
        self.assertEquals('|xyz|', config.authenticator.username_template.substitute(username='xyz'))
        self.assertEquals('dc=test', config.authenticator._base_dn)
        self.assertEquals(3, config.authenticator.version)

    def test_ldap_multiple_urls(self):
        config = _from_json({'auth': {'type': 'ldap',
                                      'url': ['http://test-ldap-1.net', 'http://test-ldap-2.net'],
                                      'username_pattern': '|$username|'}})
        self.assertIsInstance(config.authenticator, LdapAuthenticator)
        self.assertEquals(['http://test-ldap-1.net', 'http://test-ldap-2.net'], config.authenticator.url)
        self.assertEquals('|xyz|', config.authenticator.username_template.substitute(username='xyz'))

    def test_htpasswd_auth(self):
        file = test_utils.create_file('some-path', text='user1:1yL79Q78yczsM')
        config = _from_json({'auth': {'type': 'htpasswd',
                                      'htpasswd_path': file}})
        self.assertIsInstance(config.authenticator, HtpasswdAuthenticator)

        authenticated = config.authenticator.verifier.verify('user1', 'aaa')
        self.assertTrue(authenticated)

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

    def tearDown(self) -> None:
        super().tearDown()
        test_utils.cleanup()


class TestSecurityConfig(unittest.TestCase):
    def test_default_config(self):
        config = _from_json({})

        self.assertEquals('token', config.xsrf_protection)

    @parameterized.expand([
        ('token',),
        ('header',),
        ('disabled',),
    ])
    def test_xsrf_protection(self, xsrf_protection):
        config = _from_json({'security': {
            'xsrf_protection': xsrf_protection
        }})

        self.assertEquals(xsrf_protection, config.xsrf_protection)

    def test_xsrf_protection_when_unsupported(self):
        self.assertRaises(InvalidValueException, _from_json, {'security': {
            'xsrf_protection': 'something'
        }})

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

    def tearDown(self) -> None:
        super().tearDown()
        test_utils.cleanup()


class TestEnvVariables(unittest.TestCase):

    def setUp(self) -> None:
        test_utils.set_os_environ_value('VAR1', 'abcd')
        test_utils.set_os_environ_value('VAR2', 'xyz')
        test_utils.set_os_environ_value('MY_SECRET', 'qwerty')
        test_utils.set_os_environ_value('EMAIL_PWD', '1234509')
        test_utils.set_os_environ_value('EMAIL_PWD_2', '007')

    def tearDown(self):
        test_utils.cleanup()

    def test_default_config(self):
        config = _from_json({})
        env_vars = config.env_vars.build_env_vars()
        self.assertEquals(env_vars, os.environ)

    def test_config_when_safe_env_variables_used(self):
        config = _from_json({'title': '$$VAR1', 'auth': {'type': 'ldap', 'url': '$$MY_SECRET'}})

        env_vars = config.env_vars.build_env_vars()
        self.assertEquals(env_vars, os.environ)
        self.assertEqual('abcd', env_vars['VAR1'])
        self.assertEqual('qwerty', env_vars['MY_SECRET'])

        self.assertEquals(config.title, '$$VAR1')
        self.assertEquals(config.authenticator.url, '$$MY_SECRET')

    def test_config_when_unsafe_env_variables_used(self):
        config = _from_json({
            'title': '$$VAR1',
            'auth': {'type': 'google_oauth', 'secret': '$$MY_SECRET', 'client_id': '$$VAR2'},
            'alerts': {'destinations': [
                self.create_email_destination('$$EMAIL_PWD'),
                self.create_email_destination('$VAR2')
            ]},
            'callbacks': {'destinations': [
                self.create_email_destination('$$EMAIL_PWD_2'),
                self.create_email_destination('VAR1')
            ]},
            'access': {'allowed_users': '*'}
        })

        env_vars = config.env_vars.build_env_vars()
        self.assertEqual('abcd', env_vars['VAR1'])
        self.assertEqual('xyz', env_vars['VAR2'])
        self.assertNotIn('MY_SECRET', env_vars)
        self.assertNotIn('EMAIL_PWD', env_vars)
        self.assertNotIn('EMAIL_PWD_2', env_vars)

        self.assertEquals(config.title, '$$VAR1')
        self.assertEquals(config.authenticator.secret, 'qwerty')

        alert_destinations = AlertsService(config.alerts_config)._communication_service._destinations
        self.assertEquals(alert_destinations[0]._communicator.password, '1234509')
        self.assertEquals(alert_destinations[1]._communicator.password, '$VAR2')

        # noinspection PyTypeChecker
        callback_feature = ExecutionsCallbackFeature(None, config.callbacks_config, None)
        callback_destinations = callback_feature._communication_service._destinations
        self.assertEquals(callback_destinations[0]._communicator.password, '007')
        self.assertEquals(callback_destinations[1]._communicator.password, 'VAR1')

    def create_email_destination(self, password):
        return {'type': 'email',
                'password': password,
                'to': 'some_address',
                'from': 'some_address',
                'server': 'some_server'}


def _from_json(content):
    json_obj = json.dumps(content)
    conf_path = os.path.join(test_utils.temp_folder, 'conf.json')
    file_utils.write_file(conf_path, json_obj)
    return server_conf.from_json(conf_path, test_utils.temp_folder)
