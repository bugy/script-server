import sys
from unittest import TestCase, mock
from unittest.mock import patch

from parameterized import parameterized_class

from auth.auth_base import AuthRejectedError
from auth.auth_htpasswd import HtpasswdAuthenticator, _HtpasswdVerifier, _BuiltItVerifier
from model.server_conf import InvalidServerConfigException
from tests import test_utils
from utils import os_utils
from utils.process_utils import ProcessInvoker

htpasswd_content = """
user_md5_1:$apr1$ZNlsZi/u$mCrlk4G9CqrMh04WErcck0
user_md5_2:$apr1$q.vHoeCu$Zr6okeeDiMy3FW4ug1mmk.
user_md5_3:$apr1$L/.9OmZ4$xUxfseRXYCUhMZDBhy2Bt0
user_bcrypt_1:$2y$05$jZ/Dc6nLp9F9bfv2msLtCO9EovZnkaie0X/bvHo0q4Jycq6OSNUua
user_bcrypt_2:$2y$05$GnhuY28peL6Q5f0svXyX3Oz/AXwJOfrILRbFA7.hW7Ys.ZiOnjYbm
user_bcrypt_3:$2y$05$553JeSVk/7U6i3Rapij7SeZhwWUuA8IaW7UY1BDbCa8WRuAJ02AbK
user_bcrypt_4:$2y$09$6Tw5.x40ZyWlDYQ5D71faeh3hi7lk7ZXqO3HQtcYYlxucEye/frU2
user_crypt_1:1yL79Q78yczsM
user_crypt_2:Wq0Xnblam4X86
user_crypt_3:bJi18l/cInJM2
user_crypt_4:qTz.4LSilKxc.
user_sha_1:{SHA}ynOrZVaM0SXC0noiu9noY8ELZ10=
user_sha_2:{SHA}6VJno9fJA1ftvwyWTLHc4YwD7Ic=
user_sha_3:{SHA}pheMUloNXxIzxv22EDA20pK/BWo=
"""

username_passwords = {
    'user_md5_1': '111',
    'user_md5_2': '222',
    'user_md5_3': '333',
    'user_bcrypt_1': 'one',
    'user_bcrypt_2': 'two',
    'user_bcrypt_3': 'three',
    'user_bcrypt_4': 'four',
    'user_crypt_1': 'aaa',
    'user_crypt_2': 'bbb',
    'user_crypt_3': 'ccc',
    'user_crypt_4': 'some_long_password',
    'user_sha_1': 'I',
    'user_sha_2': 'II',
    'user_sha_3': 'III'
}

crypt_users = {
    'user_crypt_1': '1yL79Q78yczsM',
    'user_crypt_2': 'Wq0Xnblam4X86',
    'user_crypt_3': 'bJi18l/cInJM2',
    'user_crypt_4': 'qTz.4LSilKxc.'
}


@parameterized_class(('verifier'), [
    ('htpasswd',),
    ('built_in',)])
class TestHtpasswdAuthenticator(TestCase):
    def test_authenticate_success(self):
        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username, password in username_passwords.items():
            if username in crypt_users:
                continue

            self._assert_authenticated(username, password, authenticator)

    def test_authenticate_success_when_crypt(self):
        if self.verifier == 'htpasswd' and os_utils.is_win():
            return

        os_utils.set_linux()

        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username in crypt_users.keys():
            password = username_passwords[username]
            self._assert_authenticated(username, password, authenticator)

    def test_authenticate_success_when_plain(self):
        if self.verifier == 'htpasswd' and os_utils.is_linux():
            return

        os_utils.set_win()

        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username, password in crypt_users.items():
            self._assert_authenticated(username, password, authenticator)

    def test_authenticate_failure_when_no_password(self):
        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username in username_passwords.keys():
            self._assert_rejected(username, None, authenticator)

    def test_authenticate_failure(self):
        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username in username_passwords.keys():
            if username in crypt_users:
                continue

            self._assert_rejected(username, 'some_password', authenticator)

    def test_authenticate_failure_when_no_user(self):
        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        self._assert_rejected('my_user', 'my_pass', authenticator)

    def test_authenticate_failure_when_crypt_with_plain_password(self):
        if self.verifier == 'htpasswd' and os_utils.is_win():
            return

        os_utils.set_linux()

        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username in crypt_users.keys():
            password = crypt_users[username]
            self._assert_rejected(username, password, authenticator)

    def test_authenticate_failure_when_plain_with_crypt_password(self):
        if self.verifier == 'htpasswd' and os_utils.is_linux():
            return

        os_utils.set_win()

        authenticator = self._create_authenticator({'htpasswd_path': self.file_path})

        for username in crypt_users.keys():
            password = username_passwords[username]
            self._assert_rejected(username, password, authenticator)

    def test_missing_htpasswd_path_config(self):
        self.assertRaisesRegex(Exception, 'is required attribute', HtpasswdAuthenticator, {}, None)

    def test_htpasswd_file_not_exist(self):
        self.assertRaisesRegex(InvalidServerConfigException, 'htpasswd path does not exist', HtpasswdAuthenticator,
                               {'htpasswd_path': 'some/path'}, None)

    def test_missing_bcrypt_and_htpasswd(self):
        with patch.object(ProcessInvoker, 'invoke') as invoke_mock:
            invoke_mock.side_effect = FileNotFoundError('Program not found')

            with mock.patch.dict(sys.modules, {'bcrypt': None}):
                self.assertRaisesRegex(InvalidServerConfigException,
                                       'Please either install htpasswd utility or python bcrypt package',
                                       HtpasswdAuthenticator,
                                       {'htpasswd_path': self.file_path},
                                       test_utils.process_invoker)

    def _assert_authenticated(self, username, password, authenticator):
        try:
            request_handler = _mock_request_handler(username, password)

            username = authenticator.authenticate(request_handler)
            self.assertEqual(username, username)

        except Exception as e:
            self.fail('Failed to authorize ' + username + ': ' + str(e))

    def _assert_rejected(self, username, password, authenticator):
        request_handler = _mock_request_handler(username, password)

        try:
            with self.assertRaisesRegex(AuthRejectedError, 'Invalid credentials',
                                        msg='User ' + username + ' should be rejected, but was not'):
                authenticator.authenticate(request_handler)
        except Exception as e:
            if isinstance(e, AssertionError):
                raise e

            self.fail('Authorization for ' + username + ' failed with exception: ' + str(e))

    def _create_authenticator(self, config):
        process_invoker = test_utils.process_invoker
        if self.verifier == 'htpasswd':
            with mock.patch.dict(sys.modules, {'bcrypt': None}):
                authenticator = HtpasswdAuthenticator(config, process_invoker)

            self.assertIsInstance(authenticator.verifier, _HtpasswdVerifier)
            return authenticator

        elif self.verifier == 'built_in':
            with patch.object(ProcessInvoker, 'invoke') as invoke_mock:
                invoke_mock.side_effect = FileNotFoundError('Program not found')
                authenticator = HtpasswdAuthenticator(config, process_invoker)

            self.assertIsInstance(authenticator.verifier, _BuiltItVerifier)
            return authenticator

        else:
            raise Exception('Unsupported verifier: ' + self.verifier)

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

        self.file_path = test_utils.create_file('some_file', text=htpasswd_content)

    def tearDown(self) -> None:
        super().tearDown()
        test_utils.cleanup()
        os_utils.reset_os()


def _mock_request_handler(username, password):
    return test_utils.mock_request_handler(arguments={'username': username, 'password': password})
