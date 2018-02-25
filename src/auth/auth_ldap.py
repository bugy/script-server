import logging
from string import Template

from ldap3 import Connection, SIMPLE

from auth import auth_base
from model import model_helper

KNOWN_REJECTIONS = [
    "invalidCredentials",
    "user name is mandatory in simple bind",
    "password is mandatory in simple bind"]

LOGGER = logging.getLogger('script_server.LdapAuthorizer')


class LdapAuthenticator(auth_base.Authenticator):
    url = None
    username_template = None
    version = None

    def __init__(self, params_dict):
        super().__init__()

        self.url = model_helper.read_obligatory(params_dict, 'url', ' for LDAP auth')

        if params_dict.get("username_pattern"):
            self.username_template = Template(params_dict.get("username_pattern"))

        self.version = params_dict.get("version")
        if not self.version:
            self.version = 3

    def authenticate(self, request_handler):
        username = request_handler.get_argument('username')
        password = request_handler.get_argument('password')

        LOGGER.info('Logging in user ' + username)

        if self.username_template:
            user = self.username_template.substitute(username=username)
        else:
            user = username

        try:
            connection = Connection(
                self.url,
                user=user,
                password=password,
                authentication=SIMPLE,
                read_only=True,
                version=self.version
            )

            connection.bind()

            if connection.bound:
                connection.unbind()
                return username

            error = connection.last_error

        except Exception as e:
            error = str(e)

            if error not in KNOWN_REJECTIONS:
                LOGGER.exception('Error occurred while ldap authentication of user ' + username)

        if error in KNOWN_REJECTIONS:
            LOGGER.info('Invalid credentials for user ' + username)
            raise auth_base.AuthRejectedError('Invalid credentials')

        raise auth_base.AuthFailureError(error)
