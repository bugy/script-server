import json
import os
import random
import unittest
from unittest import TestCase
from unittest.mock import Mock, patch

import tornado
from tornado.testing import AsyncTestCase

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from auth.auth_base import AuthFailureError, AuthBadRequestException
from model.server_conf import InvalidServerConfigException
from tests import test_utils
from tests.test_utils import mock_object

if __name__ == '__main__':
    unittest.main()

mock_time = Mock()
mock_time.return_value = 10000.01

authenticators = []


def create_test_authenticator(*, dump_file=None, group_support=None, session_expire_minutes=None, auth_info_ttl=None):
    config = {
        'type': 'test_oauth',
        'url': 'some_url',
        'client_id': '1234',
        'secret': 'abcd',
        'group_search': 'script-server'
    }

    if dump_file is not None:
        config['state_dump_file'] = dump_file

    if group_support is not None:
        config['group_support'] = group_support

    if session_expire_minutes is not None:
        config['session_expire_minutes'] = session_expire_minutes

    if auth_info_ttl is not None:
        config['auth_info_ttl'] = auth_info_ttl

    authenticator = MockOauthAuthenticator(config)

    authenticators.append(authenticator)

    return authenticator


class TestAuthConfig(TestCase):
    def test_client_visible_config(self):
        authenticator = create_test_authenticator()

        client_visible_config = authenticator._client_visible_config
        self.assertEqual('1234', client_visible_config['client_id'])
        self.assertEqual('authorize_url', client_visible_config['oauth_url'])
        self.assertEqual('test_scope', client_visible_config['oauth_scope'])

    def test_config_values(self):
        dump_file_path = os.path.join(test_utils.temp_folder, 'dump.json')
        authenticator = create_test_authenticator(dump_file=dump_file_path, session_expire_minutes=10, auth_info_ttl=80)

        self.assertEqual('1234', authenticator.client_id)
        self.assertEqual('abcd', authenticator.secret)
        self.assertEqual(True, authenticator.group_support)
        self.assertEqual(80, authenticator.auth_info_ttl)
        self.assertEqual(600, authenticator.session_expire)
        self.assertEqual(dump_file_path, authenticator.dump_file)

    def test_group_support_disabled(self):
        authenticator = create_test_authenticator(group_support=False)

        self.assertEqual(False, authenticator.group_support)

    def test_no_session_expire(self):
        authenticator = create_test_authenticator()

        self.assertEqual(0, authenticator.session_expire)

    def test_dump_file_when_folder(self):
        self.assertRaisesRegex(
            InvalidServerConfigException,
            'dump FILE instead of folder',
            create_test_authenticator,
            dump_file=test_utils.temp_folder)

    def test_dump_file_when_folder_not_exists(self):
        self.assertRaisesRegex(
            InvalidServerConfigException,
            'OAuth dump file folder does not exist',
            create_test_authenticator,
            dump_file=os.path.join(test_utils.temp_folder, 'sub', 'dump.json'))

    def test_restore_dump_state_when_no_file(self):
        dump_file_path = os.path.join(test_utils.temp_folder, 'dump.json')
        authenticator = create_test_authenticator(dump_file=dump_file_path)

        self.assertEqual({}, authenticator._users)

    def test_restore_dump_state_when_multiple_users(self):
        dump_file = test_utils.create_file('dump.json', text=json.dumps(
            [{'username': 'user_X', 'groups': ['group1', 'group2'], 'last_auth_update': 123},
             {'username': 'user_Y', 'last_visit': 456}]))
        authenticator = create_test_authenticator(dump_file=dump_file)

        self.assertEqual({'user_X', 'user_Y'}, authenticator._users.keys())

        user_x_state = authenticator._users['user_X']
        self.assertEqual('user_X', user_x_state.username)
        self.assertEqual(['group1', 'group2'], user_x_state.groups)
        self.assertEqual(123, user_x_state.last_auth_update)
        self.assertEqual(None, user_x_state.last_visit)

        user_y_state = authenticator._users['user_Y']
        self.assertEqual('user_Y', user_y_state.username)
        self.assertEqual([], user_y_state.groups)
        self.assertEqual(None, user_y_state.last_auth_update)
        self.assertEqual(456, user_y_state.last_visit)

    def setUp(self) -> None:
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

        for authenticator in authenticators:
            authenticator._cleanup()


def mock_request_handler(code):
    handler_mock = mock_object()
    handler_mock.get_argument = lambda arg, default: code if arg == 'code' else None

    secure_cookies = {}

    handler_mock.get_secure_cookie = lambda cookie: secure_cookies.get(cookie)

    def set_secure_cookie(cookie, value):
        secure_cookies[cookie] = value

    handler_mock.set_secure_cookie = set_secure_cookie

    return handler_mock


class TestAuthenticate(AsyncTestCase):
    @tornado.testing.gen_test
    def test_authenticate_successful(self):
        authenticator = create_test_authenticator()
        username = yield authenticator.authenticate(mock_request_handler(code='X'))

        self.assertEqual('user_X', username)

    @tornado.testing.gen_test
    def test_authenticate_successful_different_user(self):
        authenticator = create_test_authenticator()
        username = yield authenticator.authenticate(mock_request_handler(code='Z'))

        self.assertEqual('user_Z', username)

    @tornado.testing.gen_test
    def test_authenticate_when_no_code(self):
        authenticator = create_test_authenticator()
        with self.assertRaisesRegex(AuthBadRequestException, 'Missing authorization information'):
            yield authenticator.authenticate(mock_request_handler(code=None))

    @tornado.testing.gen_test
    def test_authenticate_when_no_token(self):
        authenticator = create_test_authenticator()
        with self.assertRaisesRegex(Exception, 'Could not generate token'):
            yield authenticator.authenticate(mock_request_handler(code='W'))

    @tornado.testing.gen_test
    def test_authenticate_when_no_email(self):
        authenticator = create_test_authenticator()

        async def custom_fetch_user_info(access_token):
            return _OauthUserInfo(None, True, {})

        authenticator.fetch_user_info = custom_fetch_user_info

        with self.assertRaisesRegex(AuthFailureError, 'No email field in user response'):
            yield authenticator.authenticate(mock_request_handler(code='X'))

    @tornado.testing.gen_test
    def test_authenticate_when_not_enabled(self):
        authenticator = create_test_authenticator()
        authenticator.disabled_users.append('user_Y')

        with self.assertRaisesRegex(AuthFailureError, 'is not enabled in OAuth provider'):
            yield authenticator.authenticate(mock_request_handler(code='Y'))

    @tornado.testing.gen_test
    def test_authenticate_and_get_user_groups(self):
        authenticator = create_test_authenticator(group_support=True)
        authenticator.user_groups['user_Y'] = ['group1', 'group2']

        username = yield authenticator.authenticate(mock_request_handler(code='Y'))
        groups = authenticator.get_groups(username)
        self.assertEqual(['group1', 'group2'], groups)

    @tornado.testing.gen_test
    def test_authenticate_and_get_user_groups_when_groups_disabled(self):
        authenticator = create_test_authenticator(group_support=False)
        authenticator.user_groups['user_Y'] = ['group1', 'group2']

        username = yield authenticator.authenticate(mock_request_handler(code='Y'))
        groups = authenticator.get_groups(username)
        self.assertEqual([], groups)

    @tornado.testing.gen_test
    def test_authenticate_and_save_user_token(self):
        authenticator = create_test_authenticator(auth_info_ttl=10)

        request_handler = mock_request_handler(code='Y')
        yield authenticator.authenticate(request_handler)

        saved_token = request_handler.get_secure_cookie('token')
        self.assertEqual('22222', saved_token)

    @tornado.testing.gen_test
    def test_authenticate_and_save_user_token_when_auth_update_disabled(self):
        authenticator = create_test_authenticator(auth_info_ttl=None)

        request_handler = mock_request_handler(code='Y')
        yield authenticator.authenticate(request_handler)

        saved_token = request_handler.get_secure_cookie('token')
        self.assertIsNone(saved_token)

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

        for authenticator in authenticators:
            authenticator._cleanup()


class TestValidateUser(AsyncTestCase):
    @tornado.testing.gen_test
    def test_validate_user_success(self):
        authenticator = create_test_authenticator()

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        valid = authenticator.validate_user(username, request_handler)
        self.assertEqual(True, valid)

    @tornado.testing.gen_test
    def test_validate_when_no_state(self):
        authenticator = create_test_authenticator(group_support=False)

        valid = authenticator.validate_user('user_X', mock_request_handler(''))
        self.assertEqual(True, valid)

    @tornado.testing.gen_test
    def test_validate_when_no_username(self):
        authenticator = create_test_authenticator(group_support=False)

        valid = authenticator.validate_user(None, mock_request_handler(''))
        self.assertEqual(False, valid)

    @tornado.testing.gen_test
    def test_validate_when_no_state_and_expire_enabled(self):
        authenticator = create_test_authenticator(session_expire_minutes=1)

        valid = authenticator.validate_user('user_X', mock_request_handler(''))
        self.assertEqual(False, valid)

    @tornado.testing.gen_test
    def test_validate_when_no_state_and_auth_update_enabled(self):
        authenticator = create_test_authenticator(auth_info_ttl=1)

        valid = authenticator.validate_user('user_X', mock_request_handler(''))
        self.assertEqual(False, valid)

    @tornado.testing.gen_test
    def test_validate_when_no_state_and_group_support(self):
        authenticator = create_test_authenticator(group_support=True)

        valid = authenticator.validate_user('user_X', mock_request_handler(''))
        self.assertEqual(False, valid)

    @patch('time.time', mock_time)
    @tornado.testing.gen_test
    def test_validate_when_session_expired(self):
        authenticator = create_test_authenticator(session_expire_minutes=5)

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 10
        valid = authenticator.validate_user(username, request_handler)
        self.assertEqual(False, valid)

    @patch('time.time', mock_time)
    @tornado.testing.gen_test
    def test_validate_when_session_not_expired(self):
        authenticator = create_test_authenticator(session_expire_minutes=5)

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 2
        valid = authenticator.validate_user(username, request_handler)
        self.assertEqual(True, valid)

    @patch('time.time', mock_time)
    @tornado.testing.gen_test
    def test_validate_when_session_not_expired_after_renew(self):
        authenticator = create_test_authenticator(session_expire_minutes=5)

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 2
        authenticator.validate_user(username, request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 4
        valid2 = authenticator.validate_user(username, request_handler)
        self.assertEqual(True, valid2)

    @patch('time.time', mock_time)
    @tornado.testing.gen_test
    def test_validate_when_session_expired_after_renew(self):
        authenticator = create_test_authenticator(session_expire_minutes=5)

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 2
        authenticator.validate_user(username, request_handler)

        mock_time.return_value = mock_time.return_value + 60 * 6
        valid2 = authenticator.validate_user(username, request_handler)
        self.assertEqual(False, valid2)

    @patch('time.time', mock_time)
    @tornado.testing.gen_test
    def test_validate_when_update_auth_and_no_access_token(self):
        authenticator = create_test_authenticator(auth_info_ttl=1)

        request_handler = mock_request_handler('X')
        username = yield authenticator.authenticate(request_handler)

        valid = authenticator.validate_user(username, mock_request_handler('X'))
        self.assertEqual(False, valid)

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

        for authenticator in authenticators:
            authenticator._cleanup()


class MockOauthAuthenticator(AbstractOauthAuthenticator):
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
