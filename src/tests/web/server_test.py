import os
import threading
import traceback
from asyncio import set_event_loop_policy
from unittest import TestCase
from unittest.mock import patch

import requests
from tornado.ioloop import IOLoop

from auth.authorization import Authorizer, ANY_USER, EmptyGroupProvider
from config.config_service import ConfigService
from features.file_download_feature import FileDownloadFeature
from files.user_file_storage import UserFileStorage
from model.server_conf import ServerConfig
from tests import test_utils
from utils import os_utils, env_utils
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
            {'name': 's1', 'group': None},
            {'name': 's2', 'group': 'Xyz'},
            {'name': 's3', 'group': None}],
            response['scripts'])

    def test_redirect_honors_protocol_header(self):
        self.start_server(12345, '127.0.0.1')

        response = requests.get('http://127.0.0.1:12345/',
            allow_redirects=False,
            headers={'X-Forwarded-Proto': 'https'})
        self.assertRegex(response.headers['Location'], '^https')

    def request(self, method, url):
        response = requests.request(method, url)
        self.assertEqual(200, response.status_code, 'Failed to execute request: ' + response.text)
        return response.json()

    def check_server_running(self):
        response = requests.get('http://127.0.0.1:12345/conf')
        self.assertEqual(response.status_code, 200)

    def start_server(self, port, address):
        file_download_feature = FileDownloadFeature(UserFileStorage(b'some_secret'), test_utils.temp_folder)
        config = ServerConfig()
        config.port = port
        config.address = address

        authorizer = Authorizer(ANY_USER, [], [], EmptyGroupProvider())
        server.init(config,
                    None,
                    authorizer,
                    None,
                    None,
                    None,
                    ConfigService(authorizer, self.conf_folder),
                    None,
                    None,
                    file_download_feature,
                    'cookie_secret',
                    None,
                    self.conf_folder,
                    start_server=False)
        self.start_loop()

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
