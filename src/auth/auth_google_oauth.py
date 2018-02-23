import hashlib
import logging
import os
import urllib.parse as urllib_parse

import tornado.auth
from tornado import gen, httpclient, escape
from tornado import httputil

from auth import auth_base
from auth.auth_base import AuthRedirectedException, AuthFailureError, AuthRejectedError
from model import model_helper
from utils.tornado_utils import normalize_url

LOGGER = logging.getLogger('script_server.GoogleOauthAuthorizer')


# noinspection PyProtectedMember
class GoogleOauthAuthorizer(auth_base.Authorizer):
    def __init__(self, params_dict):
        self.client_id = model_helper.read_obligatory(params_dict, 'client_id', ' for Google OAuth')
        self.secret = model_helper.read_obligatory(params_dict, 'secret', ' for Google OAuth')
        self.states = {}

    def authenticate(self, request_handler):
        code = request_handler.get_argument('code', False)

        if not code:
            oauth_url = self._build_redirect_url(request_handler)
            raise AuthRedirectedException(redirect_url=oauth_url)
        else:
            return self.read_user(code, request_handler)

    def _build_redirect_url(self, request_handler):
        state = hashlib.sha256(os.urandom(1024)).hexdigest()

        args = {
            'redirect_uri': get_path_for_redirect(request_handler),
            'state': state,
            'client_id': self.client_id,
            'scope': 'email',
            'response_type': 'code'
        }
        google_auth_url = tornado.auth.GoogleOAuth2Mixin._OAUTH_AUTHORIZE_URL

        self.save_state(request_handler, state)

        return httputil.url_concat(google_auth_url, args)

    @gen.coroutine
    def read_user(self, code, request_handler):
        self.restore_saved_state(request_handler)

        access_token = yield self.get_access_token(code, request_handler)

        oauth_mixin = tornado.auth.GoogleOAuth2Mixin()
        user_future = oauth_mixin.oauth2_request(
            tornado.auth.GoogleOAuth2Mixin._OAUTH_USERINFO_URL,
            access_token=access_token)
        user_response = yield user_future

        if user_response.get('email'):
            return user_response.get('email')

        error_message = 'No email field in user response. The response: ' + str(user_response)
        LOGGER.error(error_message)
        raise AuthFailureError(error_message)

    @gen.coroutine
    def get_access_token(self, code, request_handler):
        body = urllib_parse.urlencode({
            'redirect_uri': get_path_for_redirect(request_handler),
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'authorization_code',
        })
        http_client = httpclient.AsyncHTTPClient()
        response = yield http_client.fetch(
            tornado.auth.GoogleOAuth2Mixin._OAUTH_ACCESS_TOKEN_URL,
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

    def save_state(self, request_handler, state_id):
        self.states[state_id] = request_handler.request.arguments

    # This method restores request arguments of the original request (from the client)
    # And also validates, that incoming request is a reply to our previous redirection
    def restore_saved_state(self, request_handler):
        state = request_handler.get_argument('state', '')
        if not state:
            message = 'Missing redirect data'
            LOGGER.error(message)
            raise AuthRejectedError(message)

        previous_arguments = self.states.pop(state, None)
        if not previous_arguments:
            message = 'Redirect data is wrong or was sent twice'
            LOGGER.error(message)
            raise AuthRejectedError(message)

        for key, value in previous_arguments.items():
            current_value = request_handler.get_argument(key, None)
            if current_value is None:
                request_handler.request.arguments[key] = value


def get_path_for_redirect(request_handler):
    request_url = request_handler.get_argument('request_url', '')
    if request_url:
        return normalize_url(request_url)

    LOGGER.warning('request_url argument is empty')
    request_handler_url = request_handler.request.protocol + "://" \
                          + request_handler.request.host \
                          + request_handler.request.path
    return normalize_url(request_handler_url)
