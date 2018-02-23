import logging
import tornado.concurrent
import tornado.escape
from tornado import gen

from auth import auth_base
from utils.tornado_utils import respond_error, redirect_relative, redirect

LOGGER = logging.getLogger('script_server.tornado_auth')


class TornadoAuth():
    def __init__(self, authorizer):
        self.authorizer = authorizer

    def is_enabled(self):
        return bool(self.authorizer)

    def is_authenticated(self, request_handler):
        if not self.is_enabled():
            return True

        username = request_handler.get_secure_cookie('username')

        return bool(username)

    def get_username(self, request_handler):
        if not self.is_enabled():
            return None

        username = request_handler.get_secure_cookie('username')
        if not username:
            return None

        return username.decode('utf-8')

    @gen.coroutine
    def authenticate(self, request_handler):
        if not self.is_enabled():
            return

        LOGGER.info('Trying to authenticate user')

        login_generic_error = 'Something went wrong. Please contact the administrator or try later'

        try:
            username = self.authorizer.authenticate(request_handler)
            if isinstance(username, tornado.concurrent.Future):
                username = yield username

        except auth_base.AuthRejectedError as e:
            respond_error(request_handler, 401, e.get_message())
            return

        except auth_base.AuthFailureError:
            respond_error(request_handler, 500, login_generic_error)
            return

        except auth_base.AuthRedirectedException as e:
            redirect(e.redirect_url, request_handler)
            return
        except:
            LOGGER.exception('Failed to call authenticate')
            respond_error(request_handler, 500, login_generic_error)
            return

        LOGGER.info('Authenticated user ' + username)

        request_handler.set_secure_cookie('username', username)

        path = tornado.escape.url_unescape(request_handler.get_argument('next', '/'))
        if path.startswith('http'):
            path = '/'

        url_fragment = request_handler.get_argument('url_fragment', '')
        if url_fragment:
            path += '#' + tornado.escape.url_unescape(url_fragment)

        redirect_relative(path, request_handler)

    def logout(self, request_handler):
        if not self.is_enabled():
            return

        username = self.get_username(request_handler)
        if not username:
            return

        LOGGER.info('Logging out ' + username)

        request_handler.clear_cookie('username')
