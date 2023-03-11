import unittest
from collections import OrderedDict

from communications.communication_model import File
from communications.destination_script import ScriptDestination
from tests import test_utils
from tests.communications.communication_test_utils import mock_communicators


@mock_communicators
class TestScriptDestination(unittest.TestCase):
    def test_send_when_list_body(self):
        body = ['param1', 'param2']
        self.do_send(body)

        self.assert_messages([body])

    def test_send_when_list_body_non_strings(self):
        body = [1, None, False]
        self.do_send(body)

        self.assert_messages([['1', 'None', 'False']])

    def test_send_when_dict_body(self):
        body = OrderedDict([('param1', 'Hello'), ('param2', 'World')])
        self.do_send(body)

        self.assert_messages([['Hello', 'World']])

    def test_send_when_dict_body_non_strings(self):
        body = OrderedDict([('param1', 123.45), ('param2', None), ('param3', False)])
        self.do_send(body)

        self.assert_messages([['123.45', 'None', 'False']])

    def test_send_3_times(self):
        self.do_send(OrderedDict([('param1', 'Hello'), ('param2', 'World')]))
        self.do_send([])
        self.do_send(['123', '456', '789'])

        self.assert_messages([['Hello', 'World'], [], ['123', '456', '789']])

    def test_send_when_string_body(self):
        self.assertRaisesRegex(Exception, 'Only dict or list bodies are supported', self.do_send, 'test message')

    def test_send_when_files(self):
        self.assertRaisesRegex(Exception, 'Files are not supported for scripts',
                               self.do_send, ['param1'], [File('test_file')])

    def test_env_when_list_body(self):
        self.do_send(['param1', 'param2'])

        self.assert_env_variables([None])

    def test_env_when_dict_body(self):
        body = OrderedDict([('param1', 'Hello'), ('param2', 'World')])
        self.do_send(body)

        self.assert_env_variables([{'param1': 'Hello', 'param2': 'World'}])

    def test_env_when_dict_body_with_non_strings(self):
        body = OrderedDict([('param1', 1), ('param2', None), ('param3', True)])
        self.do_send(body)

        self.assert_env_variables([{'param1': '1', 'param2': 'None', 'param3': 'True'}])

    def test_env_when_send_3_times(self):
        self.do_send(OrderedDict([('param1', 'Hello'), ('param2', 'World')]))
        self.do_send([])
        self.do_send({'abc': '123'})

        self.assert_env_variables([{'param1': 'Hello', 'param2': 'World'}, None, {'abc': '123'}])

    def assert_env_variables(self, env_variables):
        communicator = self.get_communicators()[0]

        actual_variables = [arg.get('environment_variables') for arg in communicator.captured_arguments]
        self.assertEqual(env_variables, actual_variables)

    def assert_messages(self, expected_bodies):
        communicator = self.get_communicators()[0]

        expected_messages = [(None, body, None) for body in expected_bodies]
        self.assertEqual(expected_messages, communicator.messages)

    def do_send(self, body, files=None):
        self.destination.send('ignored', body, files)

    def setUp(self):
        self.destination = ScriptDestination({}, test_utils.process_invoker)
