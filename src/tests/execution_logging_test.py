import logging
import os
import unittest

from execution.logging import ScriptOutputLogger
from model import external_model
from model import script_configs
from react.observable import Observable
from tests import test_utils
from utils import file_utils


class TestScriptOutputLogging(unittest.TestCase):
    def test_open(self):
        self.output_logger = self.create_logger()
        self.output_logger.start()

        self.assertTrue(self.is_file_opened())

    def test_close(self):
        self.output_logger = self.create_logger()
        self.output_logger.start()

        self.output_stream.close()

        self.assertFalse(self.is_file_opened())

    def test_simple_log(self):
        self.output_logger = self.create_logger()
        self.output_logger.start()

        self.output_stream.push('some text')
        self.output_stream.close()

        self.assertEqual(self.read_log(), 'some text')

    def test_multiple_logs(self):
        self.output_logger = self.create_logger()
        self.output_logger.start()

        self.output_stream.push('some text')
        self.output_stream.push('\nand a new line')
        self.output_stream.push(' with some long long text')
        self.output_stream.close()

        self.assertEqual(self.read_log(), 'some text\nand a new line with some long long text')

    def test_log_without_open(self):
        self.output_logger = self.create_logger()

        self.output_stream.push('some text')

        self.assertIsNone(self.read_log())

    def create_logger(self):
        self.file_path = os.path.join(test_utils.temp_folder, 'TestScriptOutputLogging.log')

        self.logger = ScriptOutputLogger(self.file_path, self.output_stream)

        return self.logger

    def read_log(self):
        if self.file_path and os.path.exists(self.file_path):
            return file_utils.read_file(self.file_path)

        return None

    def is_file_opened(self):
        if self.output_logger.log_file:
            return not self.output_logger.log_file.closed

        return False

    def setUp(self):
        self.output_stream = Observable()

        test_utils.setup()

        super().setUp()

    def tearDown(self):
        self.output_stream.close()
        self.output_logger._close()

        test_utils.cleanup()

        super().tearDown()
