import logging
import shutil
import time
from unittest.mock import MagicMock

from parameterized import parameterized
from tornado import gen
from tornado.testing import AsyncTestCase, gen_test
from tornado.web import RequestHandler

from auth.auth_keycloak_openid import KeycloakOpenidAuthenticator
from scheduling import scheduler
from tests import test_utils
from tests.test_utils import mock_request_handler
from tests.utils.mock_server import MockServer

REALM_URL = 'http://my-keycloak.net/realms/master'

access_expiration_duration = 0.1
refresh_expiration_duration = 0.6


class OauthServerMock:

    def __init__(self, mock_server: MockServer):
        super().__init__()

        self.mock_server = mock_server

        self.refresh_token_counter = 1
        self.access_token_counter = 1
        self.code_user_mapping = {}

        self.mock_server.register_mock(
            'POST',
            '/realms/master/protocol/openid-connect/token',
            response_handler=self.handle_token_request
        )

        self.mock_server.register_mock(
            'GET',
            '/realms/master/protocol/openid-connect/userinfo',
            response_handler=self.handle_userinfo_request)

        self.access_token_expiration_times = {}
        self.refresh_token_expiration_times = {}
        self.user_groups = {}
        self.deactivated_users = []

    def handle_token_request(self, request_handler):
        client_id = request_handler.get_argument('client_id')
        client_secret = request_handler.get_argument('client_secret')

        if client_id != 'my-client' or client_secret != 'top_secret':
            request_handler.set_status(400, 'Invalid client parameters')
            return

        grant_type = request_handler.get_argument('grant_type')

        if grant_type == 'refresh_token':
            refresh_token = request_handler.get_argument('refresh_token')
            if refresh_token is None:
                request_handler.set_status(401, 'No token provided')
                return

            if refresh_token not in self.refresh_token_expiration_times:
                request_handler.set_status(401, 'Invalid refresh token: ' + str(refresh_token))
                return

            if self.refresh_token_expiration_times[refresh_token] < time.time():
                request_handler.set_status(401, 'Refresh token has expired: ' + refresh_token)
                return

            token_prefix, user = self.parse_token_info(refresh_token)

        elif grant_type == 'authorization_code':
            code = request_handler.get_argument('code')
            if not code or code not in self.code_user_mapping:
                request_handler.set_status(401, 'Invalid code provided: ' + str(code))
                return

            redirect_uri = request_handler.get_argument('redirect_uri')
            if redirect_uri != 'http://localhost:5432/index.html':
                request_handler.set_status(400, 'Invalid redirect_uri: ' + str(redirect_uri))
                return

            user = self.code_user_mapping[code]
            del self.code_user_mapping[code]

            token_prefix = 'token-' + user + '|'

        else:
            request_handler.set_status(400, 'Unsupported grant type: ' + str(grant_type))
            return

        if user in self.deactivated_users:
            request_handler.set_status(401, 'User is deactivated')
            return

        self.send_tokens(token_prefix, request_handler)

    @staticmethod
    def parse_token_info(refresh_token):
        token_prefix = refresh_token.split('|')[0] + '|'
        user = token_prefix[6:-1]
        return token_prefix, user

    def send_tokens(self, token_prefix, request_handler):
        access_token = f'{token_prefix}acc-{self.access_token_counter}'
        refresh_token = f'{token_prefix}ref-{self.refresh_token_counter}'
        self.access_token_counter += 1
        self.refresh_token_counter += 1

        request_handler.write({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': access_expiration_duration,
            'refresh_expires_in': refresh_expiration_duration
        })

        self.cleanup_old_tokens(self.access_token_expiration_times, token_prefix)
        self.cleanup_old_tokens(self.refresh_token_expiration_times, token_prefix)

        self.access_token_expiration_times[access_token] = time.time() + access_expiration_duration
        self.refresh_token_expiration_times[refresh_token] = time.time() + refresh_expiration_duration

    @staticmethod
    def cleanup_old_tokens(existing_tokens_map, token_prefix):
        for key in list(existing_tokens_map.keys()):
            if key.startswith(token_prefix):
                del existing_tokens_map[key]

    def handle_userinfo_request(self, request_handler: RequestHandler):
        authorization = request_handler.request.headers.get('Authorization')
        if authorization is None:
            request_handler.set_status(401, 'No token provided')
            return

        access_token = authorization[7:]
        if access_token not in self.access_token_expiration_times:
            request_handler.set_status(401, 'Wrong token provided: ' + access_token)
            return

        if self.access_token_expiration_times[access_token] < time.time():
            request_handler.set_status(401, 'Access token has expired: ' + access_token)
            return

        _, user = self.parse_token_info(access_token)
        request_handler.write({
            'preferred_username': user,
            'groups': self.user_groups.get(user, [])
        })

    def set_groups(self, username, groups):
        self.user_groups[username] = groups

    def deactivate_user(self, username):
        if username not in self.deactivated_users:
            self.deactivated_users.append(username)

    def activate_user(self, username):
        self.deactivated_users.remove(username)


class KeycloakOauthTestCase(AsyncTestCase):

    @gen_test
    async def test_success_auth(self):
        username, _ = await self.authenticate('qwerty123')

        self.assertEqual(username, 'bugy')
        self.assertEqual(['g1', 'g2'], self.authenticator.get_groups('bugy'))

    @gen_test
    async def test_success_validate_immediately(self):
        username, request_1 = await self.authenticate('qwerty123')

        self.oauth_server.set_groups('user', ['g3'])

        valid = await  self.authenticator.validate_user(username, mock_request_handler(previous_request=request_1))
        self.assertTrue(valid)
        self.assertEqual(['g1', 'g2'], self.authenticator.get_groups('bugy'))

    @gen_test
    async def test_success_validate_after_refresh(self):
        username, request_1 = await self.authenticate('qwerty123')

        self.oauth_server.set_groups('bugy', ['g3'])

        await gen.sleep(0.4 + 0.1)

        valid_1 = await  self.authenticator.validate_user(username, mock_request_handler(previous_request=request_1))
        self.assertTrue(valid_1)

        await gen.sleep(0.1)

        self.assertEqual(['g3'], self.authenticator.get_groups('bugy'))

    @gen_test
    async def test_failed_validate_after_deactivate(self):
        username, request_1 = await self.authenticate('qwerty123')

        self.oauth_server.deactivate_user('bugy')

        await gen.sleep(access_expiration_duration + 0.1)

        valid_1 = await  self.authenticator.validate_user(username, mock_request_handler(previous_request=request_1))
        self.assertFalse(valid_1)

    @gen_test
    async def test_failed_validate_after_deactivate_when_different_users(self):
        user1, user1_request1 = await self.authenticate('qwerty123')
        user2, user2_request1 = await self.authenticate('dolphin99')

        self.oauth_server.deactivate_user('bugy')

        await gen.sleep(access_expiration_duration + 0.1)

        user1_valid = await self.authenticator.validate_user(user1,
                                                             mock_request_handler(previous_request=user1_request1))
        self.assertFalse(user1_valid)

        user2_valid = await  self.authenticator.validate_user(user2,
                                                              mock_request_handler(previous_request=user2_request1))
        self.assertTrue(user2_valid)

    @parameterized.expand([
        (0, True, True, ['g1', 'g2']),
        (0, False, True, ['g3']),
        (access_expiration_duration + 0.1, True, True, ['g1', 'g2']),
        (access_expiration_duration + 0.1, False, True, ['g3']),
        (refresh_expiration_duration + 0.1, True, False, []),
        (refresh_expiration_duration + 0.1, False, False, []),
    ])
    @gen_test
    async def test_read_tokens_from_request(self, sleep_time, has_dump, expected_validity, expected_groups):
        username, request_1 = await self.authenticate('qwerty123')

        self.authenticator._dump_state()
        shutil.copyfile(self.dump_file, self.dump_file + '.bkp')

        self.authenticator.logout(username, mock_request_handler(previous_request=request_1))
        shutil.move(self.dump_file + '.bkp', self.dump_file)

        await gen.sleep(sleep_time)

        self.oauth_server.set_groups('bugy', ['g3'])

        dump_file = self.dump_file if has_dump else None

        another_authenticator = self.create_authenticator(dump_file)
        valid = await another_authenticator.validate_user(username, mock_request_handler(previous_request=request_1))
        self.assertEqual(expected_validity, valid)

        await gen.sleep(0.1)

        self.assertEqual(expected_groups, another_authenticator.get_groups(username))

    async def authenticate(self, code):
        request = mock_request_handler(arguments={'code': code},
                                       headers={'Referer': 'http://localhost:5432/index.html'})
        username = await self.authenticator.authenticate(request)
        return username, request

    def setUp(self):
        super().setUp()
        test_utils.setup()

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s.%(msecs)06d %(levelname)s %(module)s: %(message)s')

        scheduler._sleep = MagicMock()
        scheduler._sleep.side_effect = lambda x: time.sleep(0.001)

        self.dump_file = test_utils.create_file('dump.oauth', text='{}')

        self.mock_server = MockServer()

        self.authenticator = self.create_authenticator(self.dump_file)

        self._refresh_token_request_handler = None
        self.oauth_server = OauthServerMock(self.mock_server)
        self.oauth_server.set_groups('bugy', ['g1', 'g2'])
        self.oauth_server.set_groups('yaro', ['g2'])
        self.oauth_server.code_user_mapping['qwerty123'] = 'bugy'
        self.oauth_server.code_user_mapping['dolphin99'] = 'yaro'

    def create_authenticator(self, dump_file=None):
        return KeycloakOpenidAuthenticator({
            'realm_url': self.mock_server.get_host() + '/realms/master',
            'client_id': 'my-client',
            'secret': 'top_secret',
            'group_support': True,
            'auth_info_ttl': 0.4,
            'state_dump_file': dump_file
        })

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

        scheduler._sleep = time.sleep

        self.mock_server.cleanup()
