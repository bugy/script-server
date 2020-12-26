import os
import threading
import unittest

from execution.process_pty import PtyProcessWrapper
from react.observable import read_until_closed
from tests import test_utils
from utils import file_utils


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
