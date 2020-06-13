import abc
import json
import logging
import os
import threading
import time
import urllib.parse as urllib_parse
from collections import namedtuple, defaultdict
from typing import Dict

import tornado
import tornado.ioloop
from tornado import httpclient, escape

from auth import auth_base
from auth.auth_base import AuthFailureError, AuthBadRequestException
from model import model_helper
from model.model_helper import read_bool_from_config, read_int_from_config
from model.server_conf import InvalidServerConfigException
from utils import file_utils

LOGGER = logging.getLogger('script_server.AbstractOauthAuthenticator')


class _UserState:
    def __init__(self, username) -> None:
        self.username = username
        self.groups = []
        self.last_auth_update = None
        self.last_visit = None


_OauthUserInfo = namedtuple('_OauthUserInfo', ['email', 'enabled', 'oauth_response'])


def _start_timer(callback):
    timer = threading.Timer(30, callback)
    timer.setDaemon(True)
    timer.start()
    return timer


class AbstractOauthAuthenticator(auth_base.Authenticator, metaclass=abc.ABCMeta):
    def __init__(self, oauth_authorize_url, oauth_token_url, oauth_scope, params_dict):
        super().__init__()

        self.oauth_token_url = oauth_token_url
        self.oauth_scope = oauth_scope

        self.client_id = model_helper.read_obligatory(params_dict, 'client_id', ' for OAuth')
        secret_value = model_helper.read_obligatory(params_dict, 'secret', ' for OAuth')
        self.secret = model_helper.resolve_env_vars(secret_value, full_match=True)

        self._client_visible_config['client_id'] = self.client_id
        self._client_visible_config['oauth_url'] = oauth_authorize_url
        self._client_visible_config['oauth_scope'] = oauth_scope

        self.group_support = read_bool_from_config('group_support', params_dict, default=True)
        self.auth_info_ttl = params_dict.get('auth_info_ttl')
        self.session_expire = read_int_from_config('session_expire_minutes', params_dict, default=0) * 60
        self.dump_file = params_dict.get('state_dump_file')

        if self.dump_file:
            self._validate_dump_file(self.dump_file)

        self._users = {}  # type: Dict[str, _UserState]
        self._user_locks = defaultdict(lambda: threading.Lock())

        self.timer = None
        if self.dump_file:
            self._restore_state()

            self._schedule_dump_task()

    @staticmethod
    def _validate_dump_file(dump_file):
        if os.path.isdir(dump_file):
            raise InvalidServerConfigException('Please specify dump FILE instead of folder for OAuth')
        dump_folder = os.path.abspath(os.path.dirname(dump_file))
        if not os.path.exists(dump_folder):
            raise InvalidServerConfigException('OAuth dump file folder does not exist: ' + dump_folder)

    async def authenticate(self, request_handler):
        code = request_handler.get_argument('code', False)

        if not code:
            LOGGER.error('Code is not specified')
            raise AuthBadRequestException('Missing authorization information. Please contact your administrator')

        access_token = await self.fetch_access_token(code, request_handler)
        user_info = await self.fetch_user_info(access_token)

        user_email = user_info.email
        if not user_email:
            error_message = 'No email field in user response. The response: ' + str(user_info.oauth_response)
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        if not user_info.enabled:
            error_message = 'User %s is not enabled in OAuth provider. The response: %s' \
                            % (user_email, str(user_info.oauth_response))
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        user_state = _UserState(user_email)
        self._users[user_email] = user_state

        if self.group_support:
            user_groups = await self.fetch_user_groups(access_token)
            user_state.groups = user_groups

        now = time.time()

        if self.auth_info_ttl:
            request_handler.set_secure_cookie('token', access_token)
            user_state.last_auth_update = now

        user_state.last_visit = now

        return user_email

    def validate_user(self, user, request_handler):
        if not user:
            LOGGER.warning('Username is not available')
            return False

        now = time.time()

        user_state = self._users.get(user)
        if not user_state:
            # if nothing is enabled, it's ok not to have user state (e.g. after server restart)
            if self.session_expire <= 0 and not self.auth_info_ttl and not self.group_support:
                return True
            else:
                LOGGER.info('User %s state is missing', user)
                return False

        if self.session_expire > 0:
            last_visit = user_state.last_visit
            if (last_visit is None) or ((last_visit + self.session_expire) < now):
                LOGGER.info('User %s state is expired', user)
                return False

        user_state.last_visit = now

        if self.auth_info_ttl:
            access_token = request_handler.get_secure_cookie('token')
            if access_token is None:
                LOGGER.info('User %s token is not available', user)
                return False

            self.update_user_auth(user, user_state, access_token)

        return True

    def get_groups(self, user, known_groups=None):
        user_state = self._users.get(user)
        if not user_state:
            return []

        return user_state.groups

    def logout(self, user, request_handler):
        request_handler.clear_cookie('token')
        self._remove_user(user)

        self._dump_state()

    def _remove_user(self, user):
        if user in self._users:
            del self._users[user]

    async def fetch_access_token(self, code, request_handler):
        body = urllib_parse.urlencode({
            'redirect_uri': get_path_for_redirect(request_handler),
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'authorization_code',
        })
        http_client = httpclient.AsyncHTTPClient()
        response = await http_client.fetch(
            self.oauth_token_url,
            method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            body=body,
            raise_error=False)

        response_values = {}
        if response.body:
            response_values = escape.json_decode(response.body)

        if response.error:
            if response_values.get('error_description'):
                error_text = response_values.get('error_description')
            elif response_values.get('error'):
                error_text = response_values.get('error')
            else:
                error_text = str(response.error)

            error_message = 'Failed to load access_token: ' + error_text
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        response_values = escape.json_decode(response.body)
        access_token = response_values.get('access_token')

        if not access_token:
            message = 'No access token in response: ' + str(response.body)
            LOGGER.error(message)
            raise AuthFailureError(message)

        return access_token

    def update_user_auth(self, username, user_state, access_token):
        now = time.time()
        ttl_expired = (user_state.last_auth_update is None) \
                      or ((user_state.last_auth_update + self.auth_info_ttl) < now)

        if not ttl_expired:
            return

        tornado.ioloop.IOLoop.current().add_callback(
            self._do_update_user_auth_async,
            username,
            user_state,
            access_token)

    async def _do_update_user_auth_async(self, username, user_state, access_token):
        lock = self._user_locks[username]

        with lock:
            now = time.time()

            ttl_expired = (user_state.last_auth_update is None) \
                          or ((user_state.last_auth_update + self.auth_info_ttl) < now)

            if not ttl_expired:
                return

            LOGGER.info('User %s state expired, refreshing', username)

            user_info = await self.fetch_user_info(access_token)  # type: _OauthUserInfo
            if (not user_info) or (not user_info.email):
                LOGGER.error('Failed to fetch user info: %s', str(user_info))
                self._remove_user(username)
                return

            if not user_info.enabled:
                LOGGER.error('User %s, was deactivated on OAuth server. New state: %s', username,
                             str(user_info.oauth_response))
                self._remove_user(username)
                return

            if self.group_support:
                try:
                    user_groups = await self.fetch_user_groups(access_token)
                    user_state.groups = user_groups
                except AuthFailureError:
                    LOGGER.error('Failed to fetch user %s groups', username)
                    self._remove_user(username)
                    return

            user_state.last_auth_update = now

    def _restore_state(self):
        if not os.path.exists(self.dump_file):
            LOGGER.info('OAuth dump file is missing. Nothing to restore')
            return

        dump_data = file_utils.read_file(self.dump_file)
        dump_json = json.loads(dump_data)

        for user_state in dump_json:
            username = user_state.get('username')
            if not username:
                LOGGER.warning('Missing username in ' + str(user_state))
                continue

            state = _UserState(username)
            self._users[username] = state
            state.groups = user_state.get('groups', [])
            state.last_auth_update = user_state.get('last_auth_update')
            state.last_visit = user_state.get('last_visit')

    def _schedule_dump_task(self):
        def repeating_dump():
            try:
                self._dump_state()
            finally:
                self._schedule_dump_task()

        self.timer = _start_timer(repeating_dump)

    def _dump_state(self):
        if self.dump_file:
            states = [s.__dict__ for s in self._users.values()]
            state_json = json.dumps(states)
            file_utils.write_file(self.dump_file, state_json)

    @abc.abstractmethod
    async def fetch_user_info(self, access_token: str) -> _OauthUserInfo:
        pass

    @abc.abstractmethod
    async def fetch_user_groups(self, access_token):
        pass

    # Tests only
    def _cleanup(self):
        if self.timer:
            self.timer.cancel()


def get_path_for_redirect(request_handler):
    referer = request_handler.request.headers.get('Referer')
    if not referer:
        LOGGER.error('No referer')
        raise AuthFailureError('Missing request header. Please contact system administrator')

    parse_result = urllib_parse.urlparse(referer)
    protocol = parse_result[0]
    host = parse_result[1]
    path = parse_result[2]

    return urllib_parse.urlunparse((protocol, host, path, '', '', ''))
