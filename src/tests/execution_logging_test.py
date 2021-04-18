import functools
import inspect
import os
import traceback
import unittest
import uuid
from datetime import datetime, timedelta
from typing import Optional

from auth.authorization import Authorizer, EmptyGroupProvider
from auth.user import User
from execution import executor
from execution.execution_service import ExecutionService
from execution.logging import ScriptOutputLogger, ExecutionLoggingService, OUTPUT_STARTED_MARKER, \
    LogNameCreator, ExecutionLoggingController
from model.model_helper import AccessProhibitedException
from model.script_config import OUTPUT_FORMAT_TERMINAL
from react.observable import Observable
from tests import test_utils
from tests.test_utils import _IdGeneratorMock, create_config_model, _MockProcessWrapper, create_audit_names, \
    create_script_param_config, wait_observable_close_notification, AnyUserAuthorizer
from utils import file_utils, audit_utils
from utils.date_utils import get_current_millis, ms_to_datetime, to_millis

USER_X = User('userX', [])


def default_values_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        spec = inspect.getfullargspec(func)
        defaults = spec.kwonlydefaults

        for key, value in defaults.items():
            if key in kwargs and kwargs[key] is None:
                kwargs[key] = value

        return func(self, *args, **kwargs)

    return wrapper


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

    def test_caret_return(self):
        self.output_logger = self.create_logger()
        self.output_logger.start()

        self.output_stream.push('some text\r')
        self.output_stream.push('another text')
        self.output_stream.close()

        self.assertEqual(self.read_log(), 'some text\ranother text')

    def create_logger(self):
        self.file_path = os.path.join(test_utils.temp_folder, 'TestScriptOutputLogging.log')

        self.logger = ScriptOutputLogger(self.file_path, self.output_stream)

        return self.logger

    def read_log(self):
        if self.file_path and os.path.exists(self.file_path):
            return file_utils.read_file(self.file_path, keep_newlines=True)

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


def _replace_line_separators(files, original, new):
    for file in files:
        content = file_utils.read_file(file, byte_content=True)
        replaced_content = content.decode('utf-8').replace(original, new).encode('utf-8')
        file_utils.write_file(file, replaced_content, byte_content=True)


class TestLoggingService(unittest.TestCase):
    def test_no_history_entries(self):
        entries = self.logging_service.get_history_entries('userX')
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

    def test_write_log_with_caret_return(self):
        self.simulate_logging(log_lines=['line 1\r', 'some text\r'])

        log_file = self.get_log_files()[0]
        log_content = self.read_logs_only(log_file)
        self.assertEqual('line 1\r\nsome text\r\n', log_content)

    def test_when_different_users_then_independent_files(self):
        self.simulate_logging(user_name='user1', log_lines=['text for user1'])
        self.simulate_logging(user_name='user2', log_lines=['user2 message'])

        user1_log_file = self.get_log_files('user1')[0]
        self.assertEqual('text for user1\n', self.read_logs_only(user1_log_file))

        user2_log_file = self.get_log_files('user2')[0]
        self.assertEqual('user2 message\n', self.read_logs_only(user2_log_file))

    def test_get_history_entries_when_one(self):
        start_time = get_current_millis()

        self.simulate_logging(execution_id='id1',
                              user_name='user1',
                              script_name='My script',
                              log_lines=['some text'],
                              start_time_millis=start_time,
                              command='./script.sh -p p1 --flag',
                              output_format='html')
        entries = self.logging_service.get_history_entries('user1')
        self.assertEqual(1, len(entries))

        entry = entries[0]
        self.validate_history_entry(entry,
                                    id='id1',
                                    user_name='user1',
                                    script_name='My script',
                                    start_time=start_time,
                                    command='./script.sh -p p1 --flag',
                                    output_format='html')

    def test_no_history_for_wrong_file(self):
        log_path = os.path.join(test_utils.temp_folder, 'wrong.log')
        file_utils.write_file(log_path, 'log\ntext\n')

        logs = self.logging_service.get_history_entries('userX')
        self.assertEqual(0, len(logs))

    def test_multiline_command_in_history(self):
        self.simulate_logging(execution_id='id1', command='./script.sh -p a\nb -p2 "\n\n\n"')
        entries = self.logging_service.get_history_entries('userX')
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
        self.simulate_logging(execution_id='1', log_lines=['text'], exit_code=13)

        entry = self.logging_service.get_history_entries('userX')[0]
        self.validate_history_entry(entry, id='1', exit_code=13)

    def test_exit_code_when_no_post_execution_call(self):
        self.simulate_logging(execution_id='1', log_lines=['text'], exit_code=13, write_post_execution_info=False)

        entry = self.logging_service.get_history_entries('userX')[0]
        self.validate_history_entry(entry, id='1', exit_code=None)

    def test_write_post_execution_info_before_log_closed(self):
        output_stream = Observable()

        execution_id = '999'
        self.start_logging(output_stream, execution_id=execution_id)

        output_stream.push('abcde')

        self.logging_service.write_post_execution_info(execution_id, 255)

        old_entry = self.logging_service.find_history_entry(execution_id, 'userX')
        self.validate_history_entry(old_entry, id=execution_id, exit_code=None)

        output_stream.close()
        new_entry = self.logging_service.find_history_entry(execution_id, 'userX')
        self.validate_history_entry(new_entry, id=execution_id, exit_code=255)

    def test_write_post_execution_info_for_unknown_id(self):
        self.logging_service.write_post_execution_info('999', 13)

    def test_history_entries_after_restart(self):
        self.simulate_logging(execution_id='id1')

        new_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator(), self.authorizer)
        entry = new_service.get_history_entries('userX')[0]
        self.validate_history_entry(entry, id='id1')

    def test_get_history_entries_after_delete(self):
        self.simulate_logging(execution_id='id1')

        for file in os.listdir(test_utils.temp_folder):
            os.remove(os.path.join(test_utils.temp_folder, file))

        entries = self.logging_service.get_history_entries('userX')
        self.assertCountEqual([], entries)

    def test_get_history_entries_only_for_current_user(self):
        self.simulate_logging(execution_id='id1', user_id='userA')
        self.simulate_logging(execution_id='id2', user_id='userB')
        self.simulate_logging(execution_id='id3', user_id='userC')
        self.simulate_logging(execution_id='id4', user_id='userA')

        entries = self._get_entries_sorted('userA')
        self.assertEquals(2, len(entries))

        self.validate_history_entry(entry=entries[0], id='id1', user_id='userA')
        self.validate_history_entry(entry=entries[1], id='id4', user_id='userA')

    def test_get_history_entries_for_power_user(self):
        self.simulate_logging(execution_id='id1', user_id='userA')
        self.simulate_logging(execution_id='id2', user_id='userB')
        self.simulate_logging(execution_id='id3', user_id='userC')
        self.simulate_logging(execution_id='id4', user_id='userA')

        entries = self._get_entries_sorted('power_user')
        self.assertEquals(4, len(entries))

        self.validate_history_entry(entry=entries[0], id='id1', user_id='userA')
        self.validate_history_entry(entry=entries[1], id='id2', user_id='userB')
        self.validate_history_entry(entry=entries[2], id='id3', user_id='userC')
        self.validate_history_entry(entry=entries[3], id='id4', user_id='userA')

    def test_get_history_entries_for_system_call(self):
        self.simulate_logging(execution_id='id1', user_id='userA')
        self.simulate_logging(execution_id='id2', user_id='userB')
        self.simulate_logging(execution_id='id3', user_id='userC')
        self.simulate_logging(execution_id='id4', user_id='userA')

        entries = self._get_entries_sorted('some user', system_call=True)
        self.assertEquals(4, len(entries))

        self.validate_history_entry(entry=entries[0], id='id1', user_id='userA')
        self.validate_history_entry(entry=entries[1], id='id2', user_id='userB')
        self.validate_history_entry(entry=entries[2], id='id3', user_id='userC')
        self.validate_history_entry(entry=entries[3], id='id4', user_id='userA')

    def test_find_history_entry_after_delete(self):
        self.simulate_logging(execution_id='id1')

        for file in os.listdir(test_utils.temp_folder):
            os.remove(os.path.join(test_utils.temp_folder, file))

        entry = self.logging_service.find_history_entry('id1', 'userX')
        self.assertIsNone(entry)

    def test_find_history_entry(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id1', 'userX')
        self.assertIsNotNone(entry)
        self.validate_history_entry(entry, id='id1')

    def test_not_find_history_entry(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id2', 'userX')
        self.assertIsNone(entry)

    def test_find_history_entry_after_restart(self):
        self.simulate_logging(execution_id='id1')

        new_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator(), self.authorizer)
        entry = new_service.find_history_entry('id1', 'userX')
        self.assertIsNotNone(entry)
        self.validate_history_entry(entry, id='id1')

    def test_entry_time_when_timezone(self):
        start_time_with_tz = datetime.strptime('2018-04-03T18:25:22+0230', "%Y-%m-%dT%H:%M:%S%z")
        self.simulate_logging(execution_id='id1', start_time_millis=to_millis(start_time_with_tz))

        entry = self.logging_service.find_history_entry('id1', 'userX')
        self.assertEqual(entry.start_time, start_time_with_tz)
        self.assertEqual(entry.start_time.utcoffset(), timedelta(hours=0, minutes=0))

    def test_entry_with_user_id_name_different(self):
        self.simulate_logging(execution_id='id1', user_name='userX', user_id='192.168.2.12')

        entry = self.logging_service.find_history_entry('id1', '192.168.2.12')
        self.validate_history_entry(entry, id='id1', user_name='userX', user_id='192.168.2.12')

    def test_find_entry_when_windows_line_seperator(self):
        self.simulate_logging(execution_id='id1', user_name='userX', user_id='192.168.2.12')
        _replace_line_separators(self.get_log_files(), '\n', '\r\n')

        entry = self.logging_service.find_history_entry('id1', '192.168.2.12')
        self.validate_history_entry(entry, id='id1', user_name='userX', user_id='192.168.2.12')

    def test_find_entry_when_another_user(self):
        self.simulate_logging(execution_id='id1')

        self.assertRaises(AccessProhibitedException, self.logging_service.find_history_entry, 'id1', 'user_a')

    def test_find_entry_when_another_user_and_has_full_access(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id1', 'power_user')
        self.validate_history_entry(entry, id='id1', user_name='userX')

    def test_find_entry_when_another_user_and_no_entry(self):
        self.simulate_logging(execution_id='id1')

        entry = self.logging_service.find_history_entry('id2', 'userA')
        self.assertIsNone(entry)

    def test_find_log_when_windows_line_seperator(self):
        self.simulate_logging(execution_id='id1', log_lines=['hello', 'wonderful', 'world'])
        _replace_line_separators(self.get_log_files(), '\n', '\r\n')

        log = self.logging_service.find_log('id1')
        self.assertEqual('hello\r\nwonderful\r\nworld\r\n', log)

    def validate_history_entry(self, entry, *,
                               id,
                               user_name='userX',
                               user_id=None,
                               script_name='my_script',
                               start_time='IGNORE',
                               command='cmd',
                               output_format=OUTPUT_FORMAT_TERMINAL,
                               exit_code: Optional[int] = 0):

        if user_id is None:
            user_id = user_name

        self.assertEqual(id, entry.id)
        self.assertEqual(user_name, entry.user_name)
        self.assertEqual(user_id, entry.user_id)
        self.assertEqual(script_name, entry.script_name)
        self.assertEqual(command, entry.command)
        self.assertEqual(output_format, entry.output_format)
        if start_time != 'IGNORE':
            self.assertEqual(ms_to_datetime(start_time), entry.start_time)

        self.assertEqual(exit_code, entry.exit_code)

    def read_logs_only(self, log_file):
        content = file_utils.read_file(log_file, keep_newlines=True)
        self.assertTrue(OUTPUT_STARTED_MARKER in content)
        log_start = content.index(OUTPUT_STARTED_MARKER) + len(OUTPUT_STARTED_MARKER) + 1
        return content[log_start:]

    def simulate_logging(self,
                         execution_id=None,
                         user_name=None,
                         user_id=None,
                         script_name=None,
                         command=None,
                         log_lines=None,
                         start_time_millis=None,
                         exit_code=0,
                         write_post_execution_info=True,
                         output_format=OUTPUT_FORMAT_TERMINAL):

        output_stream = Observable()

        execution_id = self.start_logging(command=command,
                                          execution_id=execution_id,
                                          output_stream=output_stream,
                                          script_name=script_name,
                                          start_time_millis=start_time_millis,
                                          user_id=user_id,
                                          user_name=user_name,
                                          output_format=output_format)

        if log_lines:
            for line in log_lines:
                output_stream.push(line + '\n')

        output_stream.close()

        if write_post_execution_info:
            self.logging_service.write_post_execution_info(execution_id, exit_code)

    @default_values_decorator
    def start_logging(self,
                      output_stream,
                      *,
                      execution_id=None,
                      user_name='userX',
                      user_id=None,
                      script_name='my_script',
                      command='cmd',
                      output_format=OUTPUT_FORMAT_TERMINAL,
                      start_time_millis=None):

        if not execution_id:
            execution_id = str(uuid.uuid1())

        if user_id is None:
            user_id = user_name

        all_audit_names = {audit_utils.AUTH_USERNAME: user_id}
        self.logging_service.start_logging(
            execution_id,
            user_name,
            user_id,
            script_name,
            command,
            output_stream,
            all_audit_names,
            output_format,
            start_time_millis)

        return execution_id

    @staticmethod
    def get_log_files(pattern=None):
        files = [os.path.join(test_utils.temp_folder, file)
                 for file in os.listdir(test_utils.temp_folder)
                 if file.lower().endswith('.log')]

        if pattern:
            files = [file for file in files
                     if pattern in os.path.basename(file)]

        return files

    def _get_entries_sorted(self, user_id, system_call=None):
        entries = self.logging_service.get_history_entries(user_id, system_call=system_call)
        entries.sort(key=lambda entry: entry.id)
        return entries

    def setUp(self):
        test_utils.setup()

        self.authorizer = Authorizer([], [], ['power_user'], EmptyGroupProvider())
        self.logging_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator(), self.authorizer)

    def tearDown(self):
        test_utils.cleanup()


class ExecutionLoggingInitiatorTest(unittest.TestCase):
    def test_start_logging_on_execution_start(self):
        execution_id = self.executor_service.start_script(
            create_config_model('my_script'),
            {},
            User('userX', create_audit_names(ip='localhost')))

        executor = self.executor_service.get_active_executor(execution_id, USER_X)
        executor.process_wrapper.finish(0)

        entry = self.logging_service.find_history_entry(execution_id, USER_X.user_id)
        self.assertIsNotNone(entry)

    def test_logging_values(self):
        param1 = create_script_param_config('p1')
        param2 = create_script_param_config('p2', param='-x')
        param3 = create_script_param_config('p3', param='-y', no_value=True)
        param4 = create_script_param_config('p4', param='-z', type='int')
        config_model = create_config_model(
            'my_script', script_command='echo', parameters=[param1, param2, param3, param4])

        execution_id = self.executor_service.start_script(
            config_model,
            {'p1': 'abc', 'p3': True, 'p4': 987},
            User('userX', create_audit_names(ip='localhost', auth_username='sandy')))

        executor = self.executor_service.get_active_executor(execution_id, USER_X)
        executor.process_wrapper._write_script_output('some text\n')
        executor.process_wrapper._write_script_output('another text')
        executor.process_wrapper.finish(0)

        wait_observable_close_notification(executor.get_anonymized_output_stream(), 2)

        entry = self.logging_service.find_history_entry(execution_id, 'userX')
        self.assertIsNotNone(entry)
        self.assertEqual('userX', entry.user_id)
        self.assertEqual('sandy', entry.user_name)
        self.assertEqual('my_script', entry.script_name)
        self.assertEqual('echo abc -y -z 987', entry.command)
        self.assertEqual('my_script', entry.script_name)

        log = self.logging_service.find_log(execution_id)
        self.assertEqual('some text\nanother text', log)

    def test_exit_code(self):
        config_model = create_config_model(
            'my_script', script_command='ls', parameters=[])

        execution_id = self.executor_service.start_script(
            config_model,
            {},
            User('userX', create_audit_names(ip='localhost')))

        executor = self.executor_service.get_active_executor(execution_id, USER_X)
        executor.process_wrapper._write_script_output('some text\n')
        executor.process_wrapper._write_script_output('another text')
        executor.process_wrapper.finish(14)

        wait_observable_close_notification(executor.get_anonymized_output_stream(), 2)

        entry = self.logging_service.find_history_entry(execution_id, 'userX')
        self.assertEqual(14, entry.exit_code)

    def setUp(self):
        test_utils.setup()

        executor._process_creator = _MockProcessWrapper

        authorizer = Authorizer([], [], [], EmptyGroupProvider())
        self.logging_service = ExecutionLoggingService(test_utils.temp_folder, LogNameCreator(), authorizer)
        self.executor_service = ExecutionService(AnyUserAuthorizer(), _IdGeneratorMock())

        self.controller = ExecutionLoggingController(self.executor_service, self.logging_service)
        self.controller.start()

    def tearDown(self):
        test_utils.cleanup()

        executions = self.executor_service.get_active_executions(USER_X.user_id)
        for execution_id in executions:
            try:
                self.executor_service.kill_script(execution_id, USER_X)
                self.executor_service.cleanup_execution(execution_id, USER_X)
            except:
                traceback.print_exc()
