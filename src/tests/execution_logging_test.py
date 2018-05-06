import os
import unittest
import uuid
from datetime import datetime, timedelta

from execution.logging import ScriptOutputLogger, ExecutionLoggingService, OUTPUT_STARTED_MARKER, \
    PostExecutionInfoProvider, LogNameCreator
from react.observable import Observable
from tests import test_utils
from utils import file_utils, audit_utils
from utils.date_utils import get_current_millis, ms_to_datetime, to_millis


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


class TestLoggingService(unittest.TestCase):
    def test_no_history_entries(self):
        entries = self.logging_service.get_history_entries()
        self.assertEqual(0, len(entries))

    def test_when_write_log_then_log_file_created(self):
        self.simulate_logging()

        log_files = self.get_log_files()
        self.assertEqual(1, len(log_files))

    def test_when_write_log_then_file_content_correct(self):
        self.simulate_logging(log_lines=['line 1', 'some text'])

        log_file = self.get_log_files()[0]
        log_content = self.read_logs_only(log_file)
        self.assertEqual('line 1\nsome text\n', log_content)

    def test_when_different_users_then_independent_files(self):
        self.simulate_logging(user='user1', log_lines=['text for user1'])
        self.simulate_logging(user='user2', log_lines=['user2 message'])

        user1_log_file = self.get_log_files('user1')[0]
        self.assertEqual('text for user1\n', self.read_logs_only(user1_log_file))

        user2_log_file = self.get_log_files('user2')[0]
        self.assertEqual('user2 message\n', self.read_logs_only(user2_log_file))

    def test_get_history_entries_when_one(self):
        start_time = get_current_millis()

        self.simulate_logging(execution_id='id1',
                              user='user1',
                              script_name='My script',
                              log_lines=['some text'],
                              start_time_millis=start_time,
                              command='./script.sh -p p1 --flag')
        entries = self.logging_service.get_history_entries()
        self.assertEqual(1, len(entries))

        entry = entries[0]
        self.validate_history_entry(entry,
                                    id='id1',
                                    user='user1',
                                    script_name='My script',
                                    start_time=start_time,
                                    command='./script.sh -p p1 --flag')

    def test_no_history_for_wrong_file(self):
        log_path = os.path.join(test_utils.temp_folder, 'wrong.log')
        file_utils.write_file(log_path, 'log\ntext\n')

        logs = self.logging_service.get_history_entries()
        self.assertEqual(0, len(logs))

    def test_multiline_command_in_history(self):
        self.simulate_logging(execution_id='id1', command='./script.sh -p a\nb -p2 "\n\n\n"')
        entries = self.logging_service.get_history_entries()
        self.assertEqual(1, len(entries))

        entry = entries[0]
        self.validate_history_entry(entry, id='id1', command='./script.sh -p a\nb -p2 "\n\n\n"')

    def test_get_log_by_id(self):
        self.simulate_logging(execution_id='id_X', log_lines=['line1', '2', '', 'END'])

        log = self.logging_service.find_log('id_X')
        self.assertEqual('line1\n2\n\nEND\n', log)

    def test_get_log_by_wrong_id(self):
        self.simulate_logging(execution_id='1', log_lines=['text'])

        log = self.logging_service.find_log('2')
        self.assertIsNone(log)

    def test_exit_code_in_history(self):
        self.exit_codes['1'] = 13
        self.simulate_logging(execution_id='1', log_lines=['text'])

        entry = self.logging_service.get_history_entries()[0]
        self.validate_history_entry(entry, id='1', exit_code=13)

    def test_history_entries_after_restart(self):
        self.simulate_logging(execution_id='id1')

        new_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator())
        entry = new_service.get_history_entries()[0]
        self.validate_history_entry(entry, id='id1')

    def test_find_history_entry(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id1')
        self.assertIsNotNone(entry)
        self.validate_history_entry(entry, id='id1')

    def test_not_find_history_entry(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id2')
        self.assertIsNone(entry)

    def test_find_history_entry_after_restart(self):
        self.simulate_logging(execution_id='id1')

        new_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator())
        entry = new_service.find_history_entry('id1')
        self.assertIsNotNone(entry)
        self.validate_history_entry(entry, id='id1')

    def test_entry_time_when_timezone(self):
        start_time_with_tz = datetime.strptime('2018-04-03T18:25:22+0230', "%Y-%m-%dT%H:%M:%S%z")
        self.simulate_logging(execution_id='id1', start_time_millis=to_millis(start_time_with_tz))

        entry = self.logging_service.find_history_entry('id1')
        self.assertEqual(entry.start_time, start_time_with_tz)
        self.assertEqual(entry.start_time.utcoffset(), timedelta(hours=0, minutes=0))

    def validate_history_entry(self, entry, *,
                               id,
                               user='userX',
                               script_name='my_script',
                               start_time='IGNORE',
                               command='cmd',
                               exit_code=0):
        self.assertEqual(id, entry.id)
        self.assertEqual(user, entry.username)
        self.assertEqual(script_name, entry.script_name)
        self.assertEqual(command, entry.command)
        if start_time != 'IGNORE':
            self.assertEqual(ms_to_datetime(start_time), entry.start_time)

        self.assertEqual(exit_code, entry.exit_code)

    def read_logs_only(self, log_file):
        content = file_utils.read_file(log_file)
        self.assertTrue(OUTPUT_STARTED_MARKER in content)
        log_start = content.index(OUTPUT_STARTED_MARKER) + len(OUTPUT_STARTED_MARKER) + 1
        return content[log_start:]

    def simulate_logging(self,
                         execution_id=None,
                         user='userX',
                         script_name='my_script',
                         command='cmd',
                         log_lines=None,
                         start_time_millis=None):
        if not execution_id:
            execution_id = str(uuid.uuid1())

        output_stream = Observable()

        all_audit_names = {}
        all_audit_names[audit_utils.AUTH_USERNAME] = user

        self.logging_service.start_logging(
            execution_id,
            user,
            script_name,
            command,
            output_stream,
            self.post_info_provider,
            all_audit_names,
            start_time_millis)

        if log_lines:
            for line in log_lines:
                output_stream.push(line + '\n')

        output_stream.close()

    @staticmethod
    def get_log_files(pattern=None):
        files = [os.path.join(test_utils.temp_folder, file)
                 for file in os.listdir(test_utils.temp_folder)
                 if file.lower().endswith('.log')]

        if pattern:
            files = [file for file in files
                     if pattern in os.path.basename(file)]

        return files

    def setUp(self):
        test_utils.setup()

        self.exit_codes = {}
        self.post_info_provider = _MapBasedPostExecInfo(self.exit_codes)

        self.logging_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator())

    def tearDown(self):
        test_utils.cleanup()


class _MapBasedPostExecInfo(PostExecutionInfoProvider):
    def __init__(self, exit_codes):
        self.exit_codes = exit_codes

    def get_exit_code(self, execution_id):
        if execution_id in self.exit_codes:
            return self.exit_codes[execution_id]

        return 0
