import json
import json
import os
import random
import unittest
from unittest import TestCase
from unittest.mock import Mock

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from model import server_conf
from model.server_conf import InvalidServerConfigException
from tests import test_utils
from utils import file_utils

if __name__ == '__main__':
    unittest.main()

mock_time = Mock()
mock_time.return_value = 10000.01
mock_request_handler = Mock(**{'get_secure_cookie.return_value': '12345'.encode()})


class TestAuthConfig(TestCase):
    def test_client_visible_config(self):
        authenticator = self.create_test_authenticator()

        client_visible_config = authenticator._client_visible_config
        self.assertEqual('1234', client_visible_config['client_id'])
        self.assertEqual('authorize_url', client_visible_config['oauth_url'])
        self.assertEqual('test_scope', client_visible_config['oauth_scope'])

    def test_config_values(self):
        dump_file_path = os.path.join(test_utils.temp_folder, 'dump.json')
        authenticator = self.create_test_authenticator(dump_file=dump_file_path, session_expire_minutes=10)

        self.assertEqual('1234', authenticator.client_id)
        self.assertEqual('abcd', authenticator.secret)
        self.assertEqual(True, authenticator.group_support)
        self.assertEqual(80, authenticator.auth_info_ttl)
        self.assertEqual(600, authenticator.session_expire)
        self.assertEqual(dump_file_path, authenticator.dump_file)

    def test_group_support_disabled(self):
        authenticator = self.create_test_authenticator(group_support=False)

        self.assertEqual(False, authenticator.group_support)

    def test_no_session_expire(self):
        authenticator = self.create_test_authenticator()

        self.assertEqual(0, authenticator.session_expire)

    def test_dump_file_when_folder(self):
        self.assertRaisesRegex(
            InvalidServerConfigException,
            'dump FILE instead of folder',
            self.create_test_authenticator,
            dump_file=test_utils.temp_folder)

    def test_dump_file_when_folder_not_exists(self):
        self.assertRaisesRegex(
            InvalidServerConfigException,
            'OAuth dump file folder does not exist',
            self.create_test_authenticator,
            dump_file=os.path.join(test_utils.temp_folder, 'sub', 'dump.json'))

    def test_restore_dump_state_when_no_file(self):
        dump_file_path = os.path.join(test_utils.temp_folder, 'dump.json')
        authenticator = self.create_test_authenticator(dump_file=dump_file_path)

        self.assertEqual({}, authenticator._users)

    def test_restore_dump_state_when_multiple_users(self):
        dump_file = test_utils.create_file('dump.json', text=json.dumps(
            [{'username': 'User_X', 'groups': ['group1', 'group2'], 'last_auth_update': 123},
             {'username': 'User_Y', 'last_visit': 456}]))
        authenticator = self.create_test_authenticator(dump_file=dump_file)

        self.assertEqual({'User_X', 'User_Y'}, authenticator._users.keys())

        user_x_state = authenticator._users['User_X']
        self.assertEqual('User_X', user_x_state.username)
        self.assertEqual(['group1', 'group2'], user_x_state.groups)
        self.assertEqual(123, user_x_state.last_auth_update)
        self.assertEqual(None, user_x_state.last_visit)

        user_y_state = authenticator._users['User_Y']
        self.assertEqual('User_Y', user_y_state.username)
        self.assertEqual([], user_y_state.groups)
        self.assertEqual(None, user_y_state.last_auth_update)
        self.assertEqual(456, user_y_state.last_visit)

    def create_test_authenticator(self, *, dump_file=None, group_support=None, session_expire_minutes=None):
        config = {
            'type': 'test_oauth',
            'url': 'some_url',
            'client_id': '1234',
            'secret': 'abcd',
            'group_search': 'script-server',
            'auth_info_ttl': 80
        }

        if dump_file is not None:
            config['state_dump_file'] = dump_file

        if group_support is not None:
            config['group_support'] = group_support

        if session_expire_minutes is not None:
            config['session_expire_minutes'] = session_expire_minutes

        authenticator = TestOauthAuthenticator(config)

        self.authenticators.append(authenticator)

        return authenticator

    def setUp(self) -> None:
        self.authenticators = []

        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

        for authenticator in self.authenticators:
            authenticator._cleanup()


def _from_json(content):
    json_obj = json.dumps(content)
    conf_path = os.path.join(test_utils.temp_folder, 'conf.json')
    file_utils.write_file(conf_path, json_obj)
    return server_conf.from_json(conf_path, test_utils.temp_folder)


class TestOauthAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        super().__init__('authorize_url', 'token_url', 'test_scope', params_dict)

        self.random_instance = random.seed(a=123)

        self.user_tokens = {
            '11111': 'user_X',
            '22222': 'user_Y',
            '33333': 'user_Z'
        }
        self.user_groups = {}
        self.disabled_users = []

    async def fetch_access_token(self, code, request_handler):
        for key, value in self.user_tokens.items():
            if value.endswith(code):
                return key

        raise Exception('Could not generate token for code ' + code + '. Make sure core is equal to user suffix')

    async def fetch_user_info(self, access_token: str) -> _OauthUserInfo:
        user = self.user_tokens[access_token]

        enabled = user not in self.disabled_users
        return _OauthUserInfo(user, enabled, {'username': user, 'access_token': access_token})

    async def fetch_user_groups(self, access_token):
        user = self.user_tokens[access_token]
        if user in self.user_groups:
            return self.user_groups[user]
        return []
