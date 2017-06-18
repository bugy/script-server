import logging
import os
import unittest

from execution.logging import ScriptOutputLogger
from model import external_model
from model import script_configs
from tests import test_utils
from utils import file_utils


class TestScriptOutputLogging(unittest.TestCase):
    def test_open(self):
        self.output_logger = self.create_output_logger()

        self.output_logger.open()

        self.assertTrue(self.is_file_opened())

    def test_close(self):
        self.output_logger = self.create_output_logger()

        self.output_logger.open()
        self.output_logger.close()

        self.assertFalse(self.is_file_opened())

    def test_simple_log(self):
        self.output_logger = self.create_output_logger()

        self.output_logger.open()
        self.output_logger.log('some text')
        self.output_logger.close()

        self.assertEqual(self.read_log(), 'some text')

    def test_multiple_logs(self):
        self.output_logger = self.create_output_logger()

        self.output_logger.open()
        self.output_logger.log('some text')
        self.output_logger.log('\nand a new line')
        self.output_logger.log(' with some long long text')
        self.output_logger.close()

        self.assertEqual(self.read_log(), 'some text\nand a new line with some long long text')

    def test_log_with_secure(self):
        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.secure = True
        self.config.add_parameter(parameter)

        self.execution_info.param_values['p1'] = 'a'

        self.output_logger = self.create_output_logger()

        self.output_logger.open()
        self.output_logger.log('a| some text')
        self.output_logger.log('\nand a new line')
        self.output_logger.log(' with some long long text |a')
        self.output_logger.close()

        self.assertEqual(self.read_log(), '******| some text\nand ****** new line with some long long text |******')

    def test_log_with_secure_ignore_whitespaces(self):
        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.secure = True
        self.config.add_parameter(parameter)

        self.execution_info.param_values['p1'] = ' '

        self.output_logger = self.create_output_logger()

        self.output_logger.open()
        self.output_logger.log('some text')
        self.output_logger.log('\nand a new line')
        self.output_logger.log(' with some long long text')
        self.output_logger.close()

        self.assertEqual(self.read_log(), 'some text\nand a new line with some long long text')

    def test_log_without_open(self):
        self.output_logger = self.create_output_logger()

        self.output_logger.log('some text')

        self.assertIsNone(self.read_log())

    def create_output_logger(self):
        logger = logging.getLogger('tests')
        logger.addHandler(logging.NullHandler())

        self.file_path = os.path.join(test_utils.temp_folder, 'TestScriptOutputLogging.log')

        return ScriptOutputLogger(self.file_path, logger, self.config, self.execution_info)

    def read_log(self):
        if self.file_path and os.path.exists(self.file_path):
            return file_utils.read_file(self.file_path)

        return None

    def is_file_opened(self):
        if self.output_logger.log_file:
            return not self.output_logger.log_file.closed

        return False

    def setUp(self):
        self.execution_info = external_model.ExecutionInfo()
        self.config = script_configs.Config()

        test_utils.setup()

        super().setUp()

    def tearDown(self):
        self.output_logger.close()

        test_utils.cleanup()

        super().tearDown()
