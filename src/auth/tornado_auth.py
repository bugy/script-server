import asyncio
import base64
import logging

import tornado.concurrent
import tornado.escape
from tornado import gen

from auth import auth_base
from utils import tornado_utils
from utils.tornado_utils import respond_error, redirect_relative

LOGGER = logging.getLogger('script_server.tornado_auth')


class TornadoAuth():
    def __init__(self, authenticator):
        self.authenticator = authenticator

    def is_enabled(self):
        return bool(self.authenticator)

    def is_authenticated(self, request_handler):
        if not self.is_enabled():
            return True

        username = self._get_current_user(request_handler)
        if not username:
            return False

        active = self.authenticator.validate_user(username, request_handler)
        if not active:
            self.logout(request_handler)

        return active

    def _get_current_user(self, request_handler):
        cookie_username = tornado_utils.get_secure_cookie(request_handler, 'username')
        if cookie_username:
            return cookie_username

        authorization_header = request_handler.request.headers.get('Authorization')
        if authorization_header and authorization_header.startswith('Basic '):
            username_password = base64.b64decode(authorization_header[6:]).decode('utf-8')
            (username, password) = username_password.split(':', 1)
            if self.authenticator.perform_basic_auth(username, password):
                return username

        return None

    def get_username(self, request_handler):
        if not self.is_enabled():
            return None

        username = self._get_current_user(request_handler)
        return username

    @gen.coroutine
    def authenticate(self, request_handler):
        if not self.is_enabled():
            return

        LOGGER.info('Trying to authenticate user')

        login_generic_error = 'Something went wrong. Please contact the administrator or try later'

        try:
            username = self.authenticator.authenticate(request_handler)
            if asyncio.iscoroutine(username):
                username = yield username

        except auth_base.AuthRejectedError as e:
            respond_error(request_handler, 401, e.get_message())
            return

        except auth_base.AuthFailureError:
            respond_error(request_handler, 500, login_generic_error)
            return

        except auth_base.AuthBadRequestException as e:
            respond_error(request_handler, 400, e.get_message())
            return

        except:
            LOGGER.exception('Failed to call authenticate')
            respond_error(request_handler, 500, login_generic_error)
            return

        LOGGER.info('Authenticated user ' + username)

        request_handler.set_secure_cookie('username', username, expires_days=self.authenticator.auth_expiration_days)

        path = tornado.escape.url_unescape(request_handler.get_argument('next', '/'))

        # redirect only to internal URLs
        if path.startswith('http'):
            path = '/'

        redirect_relative(path, request_handler)

    def get_client_visible_config(self):
        result = {'type': self.authenticator.auth_type}

        result.update(self.authenticator.get_client_visible_config())

        return result

    def logout(self, request_handler):
        if not self.is_enabled():
            return

        username = self.get_username(request_handler)
        if not username:
            return

        LOGGER.info('Logging out ' + username)

        request_handler.clear_cookie('username')

        self.authenticator.logout(username, request_handler)
