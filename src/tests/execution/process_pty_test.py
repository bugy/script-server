import os
import threading
import unittest

from execution.process_pty import PtyProcessWrapper
from react.observable import read_until_closed
from tests import test_utils
from utils import file_utils


class TestEnvironmentVariables(unittest.TestCase):

    def test_default_variables(self):
        env_dict = self.execute_and_get_passed_env({})
        home_path = os.path.expanduser('~')
        self.assertEqual(home_path, env_dict.get('HOME'))

    def test_custom_variables(self):
        env_dict = self.execute_and_get_passed_env({'test': 'abc', 'HOME': '/me/user'})
        self.assertEqual('abc', env_dict.get('test'))
        self.assertEqual('/me/user', env_dict.get('HOME'))

    def test_PYTHONUNBUFFERED(self):
        env_dict = self.execute_and_get_passed_env({})
        self.assertEqual('1', env_dict.get('PYTHONUNBUFFERED'))

    @staticmethod
    def execute_and_get_passed_env(custom_variables):
        process_wrapper = PtyProcessWrapper('tests/scripts/printenv.sh', '.', custom_variables)
        process_wrapper.start()
        thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
        thread.start()
        thread.join(timeout=0.1)
        output = ''.join(read_until_closed(process_wrapper.output_stream))
        lines = output.split('\n')
        env_dict = {line.split('=', 2)[0]: line.split('=', 2)[1] for line in lines if '=' in line}
        return env_dict


class TestPtyProcessWrapper(unittest.TestCase):
    def test_many_unicode_characters(self):
        long_unicode_text = ('ΩΨΔ\n' * 100000)
        test_utils.create_file('test.txt', text=long_unicode_text)

        process_wrapper = PtyProcessWrapper(['cat', 'test.txt'], test_utils.temp_folder, {})
        process_wrapper.start()

        thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
        thread.start()
        thread.join(timeout=0.1)

        output = ''.join(read_until_closed(process_wrapper.output_stream))
        self.assertEqual(long_unicode_text, output)

        self.assertEqual(0, process_wrapper.get_return_code())

    def test_mixed_encoding(self):
        file_path = os.path.join(test_utils.temp_folder, 'test.txt')
        file_utils.write_file(file_path,
                              b'g\xc3\xbcltig\n l\xc3\xa4uft ver\xc3\xa4ndert f\xc3\xbcr '
                              b'\xc4ndern \nPr\xfcfung g\xc3\xbcltig l\xc3\xa4uft \xe0\xa0\x80 \xf0\x92\x80\x80!',
                              byte_content=True)

        process_wrapper = PtyProcessWrapper(['cat', 'test.txt'], test_utils.temp_folder, {})
        process_wrapper.start()

        thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
        thread.start()
        thread.join(timeout=0.1)

        output = ''.join(read_until_closed(process_wrapper.output_stream))
        self.assertEqual('gültig\n läuft verändert für Ändern \nPrüfung gültig läuft ࠀ 𒀀!', output)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()
