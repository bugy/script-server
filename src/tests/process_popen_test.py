import os
import threading
import unittest

from execution.process_popen import prepare_cmd_for_win, POpenProcessWrapper
from react.observable import read_until_closed
from tests import test_utils


class TestEnvironmentVariables(unittest.TestCase):

    def test_default_variables(self):
        env_dict = self.execute_and_get_passed_env({})
        home_path = os.path.expanduser('~')
        self.assertEqual(home_path, env_dict.get('HOME'))

    def test_custom_variables(self):
        env_dict = self.execute_and_get_passed_env({'test': 'abc', 'HOME': '/me/user'})
        self.assertEqual('abc', env_dict.get('test'))
        self.assertEqual('/me/user', env_dict.get('HOME'))

    def test_custom_variables_when_hidden(self):
        with test_utils.custom_env({'MY_PASSWORD': 'qwerty', 'SOME_VAR': 'hi'}):
            env_dict = self.execute_and_get_passed_env({'test': 'abc', 'HOME': '/me/user'})
            self.assertEqual('abc', env_dict.get('test'))
            self.assertEqual('/me/user', env_dict.get('HOME'))
            self.assertNotIn('MY_PASSWORD', env_dict)
            self.assertEqual('hi', env_dict.get('SOME_VAR'))

    def test_PYTHONUNBUFFERED(self):
        env_dict = self.execute_and_get_passed_env({})
        self.assertEqual('1', env_dict.get('PYTHONUNBUFFERED'))

    @staticmethod
    def execute_and_get_passed_env(custom_variables):
        env_variables = test_utils.env_variables
        process_wrapper = POpenProcessWrapper(
            'tests/scripts/printenv.sh', '.', env_variables.build_env_vars(custom_variables))
        process_wrapper.start()
        thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
        thread.start()
        thread.join(timeout=0.1)
        output = ''.join(read_until_closed(process_wrapper.output_stream))
        lines = output.split('\n')
        env_dict = {line.split('=', 2)[0]: line.split('=', 2)[1] for line in lines if '=' in line}
        return env_dict


class TestPrepareForWindows(unittest.TestCase):
    def test_prepare_ping(self):
        (command, shell) = prepare_cmd_for_win(['ping'])

        self.assertEqual(['ping'], command)
        self.assertFalse(shell)

    def test_prepare_bat(self):
        script_path = test_utils.create_file('test.bat')
        (command, shell) = prepare_cmd_for_win([script_path])

        self.assertEqual([script_path], command)
        self.assertFalse(shell)

    def test_prepare_exe(self):
        script_path = test_utils.create_file('test.exe')
        (command, shell) = prepare_cmd_for_win([script_path])

        self.assertEqual([script_path], command)
        self.assertFalse(shell)

    def test_prepare_simple_py(self):
        script_path = test_utils.create_file('test.py')
        (command, shell) = prepare_cmd_for_win([script_path])

        self.assertEqual([script_path], command)
        self.assertTrue(shell)

    def test_prepare_py_with_ampersand_short_command(self):
        script_path = test_utils.create_file('test.py')
        (command, shell) = prepare_cmd_for_win([script_path, '&ping&'])

        self.assertEqual([script_path, '^&ping^&'], command)
        self.assertTrue(shell)

    def test_prepare_py_with_ampersand_another_command(self):
        script_path = test_utils.create_file('test.py')
        (command, shell) = prepare_cmd_for_win([script_path, '"&& dir c:"'])

        self.assertEqual([script_path, '"^&^& dir c:"'], command)
        self.assertTrue(shell)

    def setUp(self):
        test_utils.setup()

        super().setUp()

    def tearDown(self):
        test_utils.cleanup()

        super().tearDown()
