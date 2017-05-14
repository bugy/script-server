import os
import unittest

import tests.test_utils as test_utils
import utils.process_utils as process_utils


class TestSplitCommand(unittest.TestCase):
    def test_same_command(self):
        command_split = process_utils.split_command('python')

        self.assertEqual(command_split, ['python'])

    def test_full_path_command(self):
        test_utils.create_file('test.sh')

        command_split = process_utils.split_command('test.sh', test_utils.temp_folder)

        self.assertEqual(command_split, [os.path.abspath(os.path.join(test_utils.temp_folder, 'test.sh'))])

    def test_complex_command_linux(self):
        test_utils.set_linux()

        command_split = process_utils.split_command('/usr/bin/python test.py')

        self.assertEqual(command_split, ['/usr/bin/python', 'test.py'])

    def test_complex_command_win(self):
        test_utils.set_win()

        command_split = process_utils.split_command('"c:\program files\python\python.exe" test.py')

        self.assertEqual(command_split, ['"c:\program files\python\python.exe"', 'test.py'])

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


if __name__ == '__main__':
    unittest.main()
