import json
import logging
import os
import time
import urllib.parse as urllib_parse

import tornado.auth
import tornado.ioloop
from tornado.auth import OAuth2Mixin
from tornado import gen, httpclient, escape

from auth import auth_base
from auth.auth_base import AuthFailureError, AuthBadRequestException
from model import model_helper

from typing import List, Any, Dict, cast, Iterable, Union, Optional

LOGGER = logging.getLogger('script_server.GitlabAuthorizer')


class GitlabOAuth2Mixin(OAuth2Mixin):
    _OAUTH_AUTHORIZE_URL = '%s/oauth/authorize'
    _OAUTH_ACCESS_TOKEN_URL = '%s/oauth/token'
    _OAUTH_GITLAB_USERINFO = '%s/api/v4/user'
    _OAUTH_GITLAB_GROUPS = '%s/api/v4/groups'
    _GITLAB_PREFIX = 'https://gitlab.com'

    async def oauth2_request(self, url: str, access_token: str = None, post_args: Dict[str, Any] = None,
                             **args: Any) -> Any:
        try:
            return await super().oauth2_request(url, access_token, post_args, **args)
        except tornado.httpclient.HTTPClientError as e:
            LOGGER.error("HTTP error " + str(e.message))
            return None

    async def get_authenticated_user(
            self,
            redirect_uri: str,
            client_id: str,
            client_secret: str,
            code: str,
            extra_fields: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        http = self.get_auth_http_client()
        args = {
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
        }

        fields = {"id", "username", "name", "email", "state"}
        if extra_fields:
            fields.update(extra_fields)

        body = urllib_parse.urlencode(args)
        http_client = httpclient.AsyncHTTPClient()
        response = await http_client.fetch(
            self._OAUTH_ACCESS_TOKEN_URL % self._GITLAB_PREFIX,
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

        access_token = response_values.get('access_token')

        if not access_token:
            message = 'No access token in response: ' + str(response.body)
            LOGGER.error(message)
            raise AuthFailureError(message)

        user = await self.oauth2_request(
            self._OAUTH_GITLAB_USERINFO % self._GITLAB_PREFIX,
            access_token)

        if user is None:
            error_message = 'Failed to load user info'
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        fieldmap = response_values
        for field in fields:
            fieldmap[field] = user.get(field)

        return fieldmap


# noinspection PyProtectedMember
class GitlabOAuthAuthenticator(auth_base.Authenticator, GitlabOAuth2Mixin):
    def __init__(self, params_dict):
        super().__init__()

        LOGGER.debug("Init gitlab oauth provider with " + str(params_dict))

        self.client_id = model_helper.read_obligatory(params_dict, 'client_id', ' for Gitlab OAuth')

        secret_value = model_helper.read_obligatory(params_dict, 'secret', ' for Gitlab OAuth')
        self.secret = model_helper.resolve_env_vars(secret_value, full_match=True)

        gitlabPrefix = params_dict.get('url')
        if not model_helper.is_empty(gitlabPrefix):
            self._GITLAB_PREFIX = gitlabPrefix

        self.states = {}
        self.user_states = {}
        self.gitlab_update = params_dict.get('ttl', 60)
        self.gitlab_dump = params_dict.get('dump')
        self.session_expire = int(params_dict.get('session_expire_min', 0)) * 60

        if self.gitlab_dump and os.path.exists(self.gitlab_dump):
            dumpFile = open(self.gitlab_dump, "r")
            stateStr = dumpFile.read()
            self.user_states = escape.json_decode(stateStr)
            dumpFile.close()
            LOGGER.info("Readed state from file %s: " % self.gitlab_dump + stateStr)

        self.gitlab_group_search = params_dict.get('group_search')

        self._client_visible_config['client_id'] = self.client_id
        self._client_visible_config['oauth_url'] = self._OAUTH_AUTHORIZE_URL % self._GITLAB_PREFIX
        self._client_visible_config['oauth_scope'] = 'api'

    def authenticate(self, request_handler):
        code = request_handler.get_argument('code', False)

        if not code:
            LOGGER.error('Code is not specified')
            raise AuthBadRequestException('Missing authorization information. Please contact your administrator')

        return self.validate_user(code, request_handler)

    def is_active(self, user):
        if self.user_states.get(user) is None:
            LOGGER.info("User %s not found in state" % user)
            return False
        if self.user_states[user]['groups'] is None:
            LOGGER.info("User %s state without groups" % user)
            return False
        now = time.time()
        if self.session_expire and (self.user_states[user]['visit'] + self.session_expire) < now:
            del self.user_states[user]
            LOGGER.info("User %s session expired, logged out" % user)
            self.dump_sessions_to_file()
            return False
        self.user_states[user]['visit'] = now
        return True

    def get_groups(self, user, known_groups=None):
        if self.user_states.get(user) is None:
            return []
        now = time.time()
        if (self.user_states[user]['updated'] + self.gitlab_update) < now and not self.user_states[user]['updating']:
            self.user_states[user]['updating'] = True
            tornado.ioloop.IOLoop.current().spawn_callback(self.update_state, user)
        return self.user_states[user]['groups']

    def clean_expired_sessions(self):
        now = time.time()
        if self.session_expire:
            for userData in list(self.user_states.keys()):
                if (self.user_states[userData]['visit'] + self.session_expire) < now:
                    LOGGER.debug("User %s session expired and removed" % userData)
                    del self.user_states[userData]

    def dump_sessions_to_file(self):
        if self.gitlab_dump:
            dumpFile = open(self.gitlab_dump, "w")
            dumpFile.write(escape.json_encode(self.user_states))
            dumpFile.close()
            LOGGER.debug("Dumped state to file %s" % self.gitlab_dump)

    @gen.coroutine
    def update_state(self, user):
        group_list = yield self.read_groups(self.user_states[user]['access_token'])
        if group_list is None:
            LOGGER.error("Failed to refresh groups for %s" % user)
        else:
            LOGGER.info("Groups for %s refreshed: " % user + str(group_list))
        now = time.time()
        self.user_states[user]['groups'] = group_list
        self.user_states[user]['updating'] = False
        self.user_states[user]['updated'] = now
        self.user_states[user]['visit'] = now
        self.clean_expired_sessions()
        self.dump_sessions_to_file()
        return

    @gen.coroutine
    def read_groups(self, access_token):
        args = {
            'access_token': access_token,
            'all_available': 'false',
            'per_page': 100,
        }
        if not self.gitlab_group_search is None:
            args['search'] = self.gitlab_group_search

        group_list_future = self.oauth2_request(
            self._OAUTH_GITLAB_GROUPS % self._GITLAB_PREFIX,
            **args
        )

        group_list = yield group_list_future

        if group_list is None:
            return None

        groups = []
        for group in group_list:
            if group.get('full_path'):
                groups.append(group['full_path'])

        return groups

    @gen.coroutine
    def validate_user(self, code, request_handler):
        user_response_future = self.get_authenticated_user(
            get_path_for_redirect(request_handler),
            self.client_id,
            self.secret,
            code
        )
        user_response = yield user_response_future

        if user_response.get('email') is None:
            error_message = 'No email field in user response. The response: ' + str(user_response)
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        user_groups = yield self.read_groups(user_response.get('access_token'))
        if user_groups is None:
            error_message = 'Cant read user groups'
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        LOGGER.info("User %s group list: " % user_response['email'] + str(user_groups))
        user_response['groups'] = user_groups
        user_response['updated'] = time.time()
        user_response['visit'] = time.time()
        user_response['updating'] = False
        self.user_states[user_response['email']] = user_response
        self.clean_expired_sessions()
        self.dump_sessions_to_file()

        return user_response['email']


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
