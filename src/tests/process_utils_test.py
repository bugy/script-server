import os
import unittest

from tests import test_utils
from utils import process_utils


class TestSplitCommand(unittest.TestCase):
    def test_same_command(self):
        command_split = process_utils.split_command('python')

        self.assertEqual(command_split, ['python'])

    def test_full_path_command(self):
        file = test_utils.create_file('test.sh')

        command_split = process_utils.split_command('test.sh', test_utils.temp_folder)

        self.assertEqual(command_split, [os.path.abspath(file)])

    def test_complex_command_linux(self):
        test_utils.set_linux()

        command_split = process_utils.split_command('/usr/bin/python test.py')

        self.assertEqual(command_split, ['/usr/bin/python', 'test.py'])

    def test_complex_command_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command('"c:\program files\python\python.exe" test.py')

        self.assertEqual(command_split, ['c:\program files\python\python.exe', 'test.py'])

    def test_unwrap_double_quotes_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command('"my script.py" "param 1"')

        self.assertEqual(command_split, ['my script.py', 'param 1'])

    def test_unwrap_single_quotes_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command("'my script.py' 'param 1'")

        self.assertEqual(command_split, ['my script.py', 'param 1'])

    def test_unwrap_single_and_quotes_separate_args_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command('"my script.py" \'param 1\'')

        self.assertEqual(command_split, ['my script.py', 'param 1'])

    def test_unwrap_single_and_quotes_same_arg_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command('\'"my script.py"\' "\'param 1\'"')

        self.assertEqual(command_split, ['"my script.py"', "'param 1'"])

    def test_allow_not_quoted_file_with_whitespaces(self):
        file = test_utils.create_file('my script.py')
        command_split = process_utils.split_command('my script.py', test_utils.temp_folder)

        self.assertEqual(command_split, [os.path.abspath(file)])

    def test_allow_not_quoted_file_with_whitespaces_win(self):
        test_utils.set_win()

        file = test_utils.create_file('my script.py')
        command_split = process_utils.split_command('my script.py', test_utils.temp_folder)

        self.assertEqual(command_split, [os.path.abspath(file)])

    def test_split_not_quoted_file_with_whitespaces_when_not_exists(self):
        command_split = process_utils.split_command('my script.py', test_utils.temp_folder)

        self.assertEqual(command_split, ['my', 'script.py'])

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


if __name__ == '__main__':
    unittest.main()
