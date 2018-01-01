import unittest

from execution.process_popen import prepare_cmd_for_win
from tests import test_utils


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
