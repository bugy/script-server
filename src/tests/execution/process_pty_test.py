import threading
import unittest

from execution.process_pty import PtyProcessWrapper
from react.observable import read_until_closed
from tests import test_utils


class TestPtyProcessWrapper(unittest.TestCase):
    def test_many_unicode_characters(self):
        long_unicode_text = ('ΩΨΔ\n' * 100000)
        test_utils.create_file('test.txt', text=long_unicode_text)

        process_wrapper = PtyProcessWrapper(['cat', 'test.txt'], test_utils.temp_folder)
        process_wrapper.start()

        thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
        thread.start()
        thread.join(timeout=0.1)

        output = ''.join(read_until_closed(process_wrapper.output_stream))
        self.assertEqual(long_unicode_text, output)

        self.assertEqual(0, process_wrapper.get_return_code())

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()
