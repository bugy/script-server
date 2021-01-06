import json
import os
from urllib.parse import quote

import tornado.concurrent
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import testing, httpserver

from auth.authorization import Authorizer, ANY_USER, EmptyGroupProvider
from auth.identification import IpBasedIdentification
from auth.tornado_auth import TornadoAuth
from config.config_service import ConfigService
from model.trusted_ips import TrustedIpValidator
from tests import test_utils
from web.script_config_socket import ScriptConfigSocket


class ScriptConfigSocketTest(testing.AsyncTestCase):
    @testing.gen_test
    def test_initial_config(self):
        self.socket = yield self._connect('Test script 1')
        response = yield self.socket.read_message()
        self.assertIsNone(self.socket.close_reason)

        self.assert_model(response, 'initialConfig')

    @testing.gen_test
    def test_initial_config_when_init_with_values(self):
        self.socket = yield self._connect('Test script 1', init_with_values=True)
        self.assert_no_messages()

        self.socket.write_message(json.dumps({
            'event': 'initialValues',
            'data': {'parameterValues': {'list 1': 'B', 'file 1': 'y', 'list 2': 'y3.txt'}}}))

        response = yield self.socket.read_message()
        self.assertIsNone(self.socket.close_reason)

        self.assert_model(response, 'initialConfig', list2_values=['y1.txt', 'y2.txt', 'y3.txt'])

    @testing.gen_test
    def test_reload_model(self):
        self.socket = yield self._connect('Test script 1')
        _ = yield self.socket.read_message()

        self.socket.write_message(json.dumps({
            'event': 'reloadModelValues',
            'data': {'clientModelId': 'abcd',
                     'parameterValues': {'list 1': 'A', 'file 1': 'z', 'list 2': 'z1.txt'}}}))

        response = yield self.socket.read_message()
        self.assertIsNone(self.socket.close_reason)

        self.assert_model(response, 'reloadedConfig',
                          list2_values=['z1.txt', 'z2.txt', 'z3.txt'],
                          external_model_id='abcd')

    def assert_model(self, response, event_type, external_model_id=None, list2_values=None):
        event = json.loads(response)
        del event['data']['id']

        if list2_values is None:
            list2_values = []

        self.assertEqual(
            {'event': event_type,
             'data': {'clientModelId': external_model_id, 'name': 'Test script 1',
                      'description': None, 'schedulable': False, 'parameters': [
                     {'name': 'text 1', 'description': None, 'withoutValue': False, 'required': True, 'default': None,
                      'type': 'text', 'min': None, 'max': None, 'max_length': None, 'values': None, 'secure': False,
                      'fileRecursive': False, 'fileType': None},
                     {'name': 'list 1', 'description': None, 'withoutValue': False, 'required': False, 'default': None,
                      'type': 'list', 'min': None, 'max': None, 'max_length': None, 'values': ['A', 'B', 'C'],
                      'secure': False, 'fileRecursive': False, 'fileType': None},
                     {'name': 'file 1', 'description': None, 'withoutValue': False, 'required': False, 'default': None,
                      'type': 'server_file', 'min': None, 'max': None, 'max_length': None, 'values': ['x', 'y', 'z'],
                      'secure': False, 'fileRecursive': False, 'fileType': None},
                     {'name': 'list 2', 'description': None, 'withoutValue': False, 'required': False, 'default': None,
                      'type': 'list', 'min': None, 'max': None, 'max_length': None, 'values': list2_values,
                      'secure': False,
                      'fileRecursive': False, 'fileType': None}]}},
            event)

    def _connect(self, script_name, init_with_values=False):
        url = 'ws://localhost:{}/scripts/{}'.format(self.port, quote(script_name))
        if init_with_values:
            url += '?initWithValues=True'

        return tornado.websocket.websocket_connect(url)

    def setUp(self):
        super().setUp()

        self.socket = None

        application = tornado.web.Application([(r'/scripts/([^/]*)', ScriptConfigSocket)],
                                              login_url='/login.html',
                                              cookie_secret='12345')
        application.auth = TornadoAuth(None)
        application.authorizer = Authorizer(ANY_USER, [], [], EmptyGroupProvider())
        application.identification = IpBasedIdentification(TrustedIpValidator(['127.0.0.1']), None)
        application.config_service = ConfigService(application.authorizer, test_utils.temp_folder)

        server = httpserver.HTTPServer(application)
        socket, self.port = testing.bind_unused_port()
        server.add_socket(socket)

        test_utils.setup()

        for dir in ['x', 'y', 'z']:
            for file in range(1, 4):
                filename = dir + str(file) + '.txt'
                test_utils.create_file(os.path.join('test1_files', dir, filename))

        test1_files_path = os.path.join(test_utils.temp_folder, 'test1_files')
        test_utils.write_script_config(
            {'name': 'Test script 1',
             'script_path': 'ls',
             'parameters': [
                 test_utils.create_script_param_config('text 1', required=True),
                 test_utils.create_script_param_config('list 1', type='list',
                                                       allowed_values=['A', 'B', 'C']),
                 test_utils.create_script_param_config('file 1', type='server_file',
                                                       file_dir=test1_files_path),
                 test_utils.create_script_param_config('list 2', type='list',
                                                       values_script='ls ' + test1_files_path + '/${file 1}')
             ]},
            'test_script_1')

    def tearDown(self) -> None:
        if self.socket:
            self.socket.close()

        super().tearDown()
        test_utils.cleanup()

    def assert_no_messages(self):
        try:
            response = yield self.socket.read_queue.get(timeout=50)
            self.fail('Non-expected message received: ' + response)
        except TimeoutError:
            self.assertIsNone(self.socket.close_reason)
