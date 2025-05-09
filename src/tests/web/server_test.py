import json
import os
import threading
import traceback
from asyncio import set_event_loop_policy
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
from parameterized import parameterized
from requests.auth import HTTPBasicAuth
from tornado.ioloop import IOLoop
from tornado.web import create_signed_value

from auth.authorization import Authorizer, ANY_USER, EmptyGroupProvider
from config.config_service import ConfigService
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from files.user_file_storage import UserFileStorage
from model.server_conf import ServerConfig, XSRF_PROTECTION_TOKEN, XSRF_PROTECTION_HEADER
from tests import test_utils
from tests.test_utils import MockAuthenticator
from utils import os_utils, env_utils, file_utils
from web import server


def is_unsupported_ioloop_exception(e):
    stacktrace = traceback.extract_tb(e.__traceback__)
    failed_method = stacktrace[-1].name
    return failed_method == 'add_reader'


class ServerTest(TestCase):
    def test_init_when_linux(self):
        test_utils.set_linux()

        try:
            self.start_server(12345, '127.0.0.1')

            if self.requires_explicit_ioloop_factory:
                self.fail('Server should NOT be startable on current environment')
            else:
                self.check_server_running()

        except NotImplementedError as e:
            if self.requires_explicit_ioloop_factory and is_unsupported_ioloop_exception(e):
                return

            raise

    @patch('utils.env_utils.sys.version_info', (3, 8, 0))
    def test_init_when_windows_and_python_3_8(self):
        test_utils.set_win()

        try:
            self.start_server(12345, '127.0.0.1')
            self.check_server_running()

        except AttributeError:
            # Linux/Mac doesn't support windows specific classes
            if not self.windows:
                return
            raise

    @patch('utils.env_utils.sys.version_info', (3, 7, 0))
    def test_init_when_windows_and_python_3_7(self):
        test_utils.set_win()

        try:
            self.start_server(12345, '127.0.0.1')

            if self.requires_explicit_ioloop_factory:
                self.fail('Server should NOT be startable on current environment')
            else:
                self.check_server_running()

        except NotImplementedError as e:
            if self.requires_explicit_ioloop_factory and is_unsupported_ioloop_exception(e):
                return

            raise

    def test_get_scripts(self):
        self.start_server(12345, '127.0.0.1')

        test_utils.write_script_config({'name': 's1'}, 's1', self.runners_folder)
        test_utils.write_script_config({'name': 's2', 'group': 'Xyz'}, 's2', self.runners_folder)
        test_utils.write_script_config({'name': 's3'}, 's3', self.runners_folder)

        response = self.request('GET', 'http://127.0.0.1:12345/scripts')
        self.assertCountEqual([
            {'name': 's1', 'group': None, 'parsing_failed': False},
            {'name': 's2', 'group': 'Xyz', 'parsing_failed': False},
            {'name': 's3', 'group': None, 'parsing_failed': False}],
            response['scripts'])

    @parameterized.expand([
        ('X-Forwarded-Proto',),
        ('X-Scheme',)])
    def test_redirect_honors_protocol_header(self, header):
        self.start_server(12345, '127.0.0.1')

        response = self._user_session.get('http://127.0.0.1:12345/',
                                          allow_redirects=False,
                                          headers={header: 'https'})
        self.assertRegex(response.headers['Location'], '^https')

    def test_xsrf_protection_when_token(self):
        self.start_server(12345, '127.0.0.1')

        test_utils.write_script_config({'name': 's1', 'script_path': 'ls'}, 's1', self.runners_folder)
        response = self._user_session.get('http://127.0.0.1:12345/scripts')

        xsrf_token = response.cookies.get('_xsrf')
        start_response = self._user_session.post(
            'http://127.0.0.1:12345/executions/start',
            data={'__script_name': 's1'},
            files=[('notafile', None)],
            headers={'X-XSRFToken': xsrf_token},
            cookies=response.cookies
        )
        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(start_response.content, b'3')

    def test_xsrf_protection_when_token_failed(self):
        self.start_server(12345, '127.0.0.1')

        test_utils.write_script_config({'name': 's1', 'script_path': 'ls'}, 's1', self.runners_folder)
        response = self._user_session.get('http://127.0.0.1:12345/scripts')

        start_response = self._user_session.post(
            'http://127.0.0.1:12345/executions/start',
            data={'__script_name': 's1'},
            files=[('notafile', None)],
            headers={'X-Requested-With': 'XMLHttpRequest'},
            cookies=response.cookies
        )
        self.assertEqual(start_response.status_code, 403)

    def test_xsrf_protection_when_header(self):
        self.start_server(12345, '127.0.0.1', xsrf_protection=XSRF_PROTECTION_HEADER)

        test_utils.write_script_config({'name': 's1', 'script_path': 'ls'}, 's1', self.runners_folder)
        self._user_session.get('http://127.0.0.1:12345/scripts')

        start_response = self._user_session.post(
            'http://127.0.0.1:12345/executions/start',
            data={'__script_name': 's1'},
            files=[('notafile', None)],
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(start_response.content, b'3')

    def test_get_script_code(self):
        self.start_server(12345, '127.0.0.1')

        script_path = test_utils.create_file('my_script.py')
        test_utils.write_script_config({'name': 's1', 'script_path': script_path}, 's1', self.runners_folder)

        response = self.request('get',
                                'http://127.0.0.1:12345/admin/scripts/s1/code',
                                self._admin_session
                                )

        self.assertEqual({'code': 'test text', 'file_path': os.path.abspath(script_path)},
                         response)

    def test_create_script_config(self):
        self.start_server(12345, '127.0.0.1')

        xsrf_token = self.get_xsrf_token(self._admin_session)

        response = self._admin_session.post(
            'http://127.0.0.1:12345/admin/scripts',
            data={'filename': 'whatever', 'config': json.dumps({
                'name': 'test conf',
                'script': {
                    'mode': 'upload_script',
                    'path': 'whatever'
                }
            })},
            files={'uploadedScript': ('my.py', b'script content')},
            headers={'X-XSRFToken': xsrf_token},
        )

        self.assertEqual(200, response.status_code)

        expected_script_path = os.path.join(test_utils.temp_folder, 'conf', 'scripts', 'my.py')

        conf_response = self.request('get', 'http://127.0.0.1:12345/admin/scripts/test%20conf',
                                     self._admin_session)
        self.assertEqual({'config': {'name': 'test conf',
                                     'script_path': expected_script_path},
                          'filename': 'test_conf.json'},
                         conf_response)

        script_content = file_utils.read_file(expected_script_path)
        self.assertEqual('script content', script_content)

    def test_update_script_config(self):
        self.start_server(12345, '127.0.0.1')

        xsrf_token = self.get_xsrf_token(self._admin_session)

        script_path = test_utils.create_file('my_script.py')
        test_utils.write_script_config({'name': 's1', 'script_path': script_path}, 's1', self.runners_folder)

        response = self._admin_session.put(
            'http://127.0.0.1:12345/admin/scripts',
            data={'filename': 's1.json', 'config': json.dumps({
                'name': 'new name',
                'script': {
                    'mode': 'new_code',
                    'path': script_path,
                    'code': 'abcdef'
                }
            })},
            headers={'X-XSRFToken': xsrf_token},
        )

        self.assertEqual(200, response.status_code)

        conf_response = self.request('get', 'http://127.0.0.1:12345/admin/scripts/new%20name',
                                     self._admin_session)
        self.assertEqual({'config': {'name': 'new name',
                                     'script_path': script_path},
                          'filename': 's1.json'},
                         conf_response)

        script_content = file_utils.read_file(script_path)
        self.assertEqual('abcdef', script_content)

    def test_on_fly_auth(self):
        self.start_server(12345, '127.0.0.1')

    def test_get_scripts_when_basic_auth(self):
        self.start_server(12345, '127.0.0.1')

        test_utils.write_script_config({'name': 's1'}, 's1', self.runners_folder)

        response = self.request('GET',
                                'http://127.0.0.1:12345/scripts',
                                session=requests.Session(),
                                auth=HTTPBasicAuth('normal_user', 'qwerty'))
        self.assertCountEqual([
            {'name': 's1', 'group': None, 'parsing_failed': False}],
            response['scripts'])

    def test_get_scripts_when_basic_auth_failure(self):
        self.start_server(12345, '127.0.0.1')

        test_utils.write_script_config({'name': 's1'}, 's1', self.runners_folder)

        response = requests.get('http://127.0.0.1:12345/scripts', auth=HTTPBasicAuth('normal_user', 'wrong_pass'))
        self.assertEqual(401, response.status_code)

    @staticmethod
    def get_xsrf_token(session):
        response = session.get('http://127.0.0.1:12345/admin/scripts')
        return response.cookies.get('_xsrf')

    def request(self, method, url, session=None, auth=None):
        if session is None:
            session = self._user_session

        response = session.request(method, url, auth=auth)
        self.assertEqual(200, response.status_code, 'Failed to execute request: ' + response.text)
        return response.json()

    def check_server_running(self):
        response = self._user_session.get('http://127.0.0.1:12345/conf')
        self.assertEqual(response.status_code, 200)

    def start_server(self, port, address, *, xsrf_protection=XSRF_PROTECTION_TOKEN):
        file_download_feature = FileDownloadFeature(UserFileStorage(b'some_secret'), test_utils.temp_folder)
        config = ServerConfig()
        config.port = port
        config.address = address
        config.xsrf_protection = xsrf_protection
        config.max_request_size_mb = 1

        authorizer = Authorizer(ANY_USER, ['admin_user'], [], ['admin_user'], EmptyGroupProvider())
        execution_service = MagicMock()
        execution_service.start_script.return_value = 3

        cookie_secret = b'cookie_secret'

        authenticator = MockAuthenticator()
        authenticator.add_user('normal_user', 'qwerty')

        server.init(config,
                    authenticator,
                    authorizer,
                    execution_service,
                    MagicMock(),
                    MagicMock(),
                    ConfigService(authorizer, self.conf_folder, True, test_utils.process_invoker),
                    MagicMock(),
                    FileUploadFeature(UserFileStorage(cookie_secret), test_utils.temp_folder),
                    file_download_feature,
                    'cookie_secret',
                    None,
                    self.conf_folder,
                    start_server=False)
        self.start_loop()

        self._user_session = requests.Session()
        self._user_session.cookies['username'] = create_signed_value(cookie_secret, 'username', 'normal_user') \
            .decode('utf8')

        self._admin_session = requests.Session()
        self._admin_session.cookies['username'] = create_signed_value(cookie_secret, 'username', 'admin_user') \
            .decode('utf8')

    def start_loop(self):
        io_loop = IOLoop.current()
        self.ioloop_thread = threading.Thread(target=io_loop.start)
        self.ioloop_thread.start()

    def setUp(self) -> None:
        super().setUp()

        test_utils.setup()
        self.requires_explicit_ioloop_factory = os_utils.is_win() and env_utils.is_min_version('3.8')
        self.windows = os_utils.is_win()

        self.conf_folder = test_utils.create_dir(os.path.join('conf'))
        self.runners_folder = os.path.join(self.conf_folder, 'runners')

    def tearDown(self) -> None:
        super().tearDown()

        io_loop = IOLoop.current()

        try:
            server._http_server.stop()
        except KeyError:
            for socket in server._http_server._sockets.values():
                socket.close()
            server._http_server._sockets.clear()

        self.kill_ioloop(io_loop)

        test_utils.cleanup()

    def kill_ioloop(self, io_loop):
        if not io_loop or not io_loop.asyncio_loop.is_running():
            return

        io_loop.add_callback(io_loop.stop)

        self.ioloop_thread.join(timeout=50)
        io_loop.close()
        set_event_loop_policy(None)
