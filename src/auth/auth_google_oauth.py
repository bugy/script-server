import logging
import urllib.parse as urllib_parse

import tornado.auth
from tornado import gen, httpclient, escape

from auth import auth_base
from auth.auth_base import AuthFailureError, AuthBadRequestException
from model import model_helper
from utils.tornado_utils import normalize_url

LOGGER = logging.getLogger('script_server.GoogleOauthAuthorizer')


# noinspection PyProtectedMember
class GoogleOauthAuthenticator(auth_base.Authenticator):
    def __init__(self, params_dict):
        super().__init__()

        self.client_id = model_helper.read_obligatory(params_dict, 'client_id', ' for Google OAuth')

        secret_value = model_helper.read_obligatory(params_dict, 'secret', ' for Google OAuth')
        self.secret = model_helper.unwrap_conf_value(secret_value)

        self.states = {}

        self.client_visible_config['client_id'] = self.client_id
        self.client_visible_config['oauth_url'] = tornado.auth.GoogleOAuth2Mixin._OAUTH_AUTHORIZE_URL
        self.client_visible_config['oauth_scope'] = 'email'

    def authenticate(self, request_handler):
        code = request_handler.get_argument('code', False)

        if not code:
            LOGGER.error('Code is not specified')
            raise AuthBadRequestException('Missing authorization information. Please contact your administrator')

        return self.read_user(code, request_handler)

    @gen.coroutine
    def read_user(self, code, request_handler):
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
