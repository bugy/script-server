import crypt
import logging
import os

from auth import auth_base
from model import model_helper
from model.server_conf import InvalidServerConfigException
from utils import process_utils, encryption_utils, os_utils
from utils.process_utils import ExecutionException
from utils.string_utils import is_blank

LOGGER = logging.getLogger('script_server.BasicAuthAuthenticator')


def _select_verifier(htpasswd_path):
    if _HtpasswdVerifier.is_installed():
        LOGGER.info('Using htpasswd utility for password verification')
        return _HtpasswdVerifier(htpasswd_path)

    LOGGER.info('Using built-in encoder for password verification')
    return _BuiltItVerifier(htpasswd_path)


class BasicAuthAuthenticator(auth_base.Authenticator):
    def __init__(self, params_dict):
        super().__init__()

        htpasswd_path = model_helper.read_obligatory(params_dict, 'htpasswd_path', ' for Basic auth')
        if not os.path.exists(htpasswd_path):
            raise InvalidServerConfigException('htpasswd path does not exist: ' + htpasswd_path)

        self.verifier = _select_verifier(htpasswd_path)

    def authenticate(self, request_handler):
        username = request_handler.get_argument('username')
        password = request_handler.get_argument('password')

        auth_error = auth_base.AuthRejectedError('Invalid credentials')

        if password is None:
            LOGGER.warning('Password was not provided for user ' + username)
            raise auth_error

        if not self.verifier.verify(username, password):
            raise auth_error

        return username


class _HtpasswdVerifier:

    def __init__(self, file_path) -> None:
        self.path = file_path

    def verify(self, username, password):
        try:
            process_utils.invoke(['htpasswd', '-bv', self.path, username, password], check_stderr=False)
            return True

        except ExecutionException as e:
            if e.exit_code in [3, 5, 6]:
                return False
            raise e

    @staticmethod
    def is_installed():
        try:
            output = process_utils.invoke(['htpasswd', '-nbp', 'some_user', 'some_password'], check_stderr=False)
            return output.strip().endswith('some_user:some_password')
        except FileNotFoundError:
            return False


class _BuiltItVerifier:

    def __init__(self, file_path) -> None:
        self.user_passwords = self._parse_htpasswd(file_path)

        for password in self.user_passwords.values():
            if password.startswith('$2y$'):
                try:
                    import bcrypt
                except ImportError:
                    raise InvalidServerConfigException('htpasswd contains bcrypt passwords. '
                                                       'Please either install htpasswd utility or python bcrypt package')

    def verify(self, username, password):
        if username not in self.user_passwords:
            LOGGER.warning('User ' + username + ' does not exist')
            return False

        existing_password = self.user_passwords.get(username)

        # Selects encryption algorithm depending on the password format
        # https://httpd.apache.org/docs/2.4/misc/password_encryptions.html
        if existing_password.startswith('$2y$'):
            import bcrypt
            return bcrypt.checkpw(password.encode('utf8'), existing_password.encode('utf8'))

        elif existing_password.startswith('$apr1$'):
            salt = existing_password[6:existing_password.find('$', 6)]
            hashed_password = encryption_utils.md5_apr1(salt, password)
            return hashed_password == existing_password

        elif existing_password.startswith('{SHA}'):
            expected = existing_password[5:]
            hashed_password = encryption_utils.sha1(password)
            return hashed_password == expected

        elif not os_utils.is_win():
            hashed_password = crypt.crypt(password, existing_password[:2])
            return hashed_password == existing_password

        else:
            return password == existing_password

    @staticmethod
    def _parse_htpasswd(htpasswd_path):
        with open(htpasswd_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if not is_blank(line)]

        result = {}
        for line in lines:
            (username, password) = line.split(':', 1)
            result[username] = password
        return result
