import time
import unittest

from execution import executor
from execution.executor import ScriptExecutor
from model import script_configs
from react.observable import _StoringObserver, read_until_closed
from tests.test_utils import _MockProcessWrapper

BUFFER_FLUSH_WAIT_TIME = (executor.TIME_BUFFER_MS * 1.5) / 1000.0


class TestBuildCommandArgs(unittest.TestCase):
    def test_no_parameters_no_values(self):
        config = script_configs.Config()

        args_string = executor.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_no_parameters_some_values(self):
        config = script_configs.Config()

        args_string = executor.build_command_args({'p1': 'value', 'p2': 'value'}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_no_values(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        config.add_parameter(parameter)

        args_string = executor.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_one_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['value'])

    def test_one_parameter_with_param(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['-p1', 'value'])

    def test_one_parameter_flag_no_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = executor.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_flag_false(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': False}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_flag_true(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': True}, config)

        self.assertEqual(args_string, ['--flag'])

    def test_parameter_constant(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.constant = True
        parameter.default = 'const'
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['const'])

    def test_parameter_int(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'int'
        config.add_parameter(parameter)

        args_string = executor.build_command_args({'p1': 5}, config)

        self.assertEqual(args_string, ['-p1', 5])

    def test_parameter_multiselect_when_empty_string(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ''}, config)

        self.assertEqual(args_list, [])

    def test_parameter_multiselect_when_empty_list(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': []}, config)

        self.assertEqual(args_list, [])

    def test_parameter_multiselect_when_single_list(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(args_list, ['-p1', 'val1'])

    def test_parameter_multiselect_when_single_list_as_multiarg(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(args_list, ['-p1', 'val1'])

    def test_parameter_multiselect_when_multiple_list(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(args_list, ['val1,val2,hello world'])

    def test_parameter_multiselect_when_multiple_list_and_custom_separator(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.type = 'multiselect'
        parameter.separator = '; '
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(args_list, ['val1; val2; hello world'])

    def test_parameter_multiselect_when_multiple_list_as_multiarg(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.type = 'multiselect'
        parameter.multiple_arguments = True
        config.add_parameter(parameter)

        args_list = executor.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(args_list, ['val1', 'val2', 'hello world'])

    def test_multiple_parameters_sequence(self):
        config = script_configs.Config()

        p1 = script_configs.Parameter()
        p1.name = 'p1'
        p1.param = '-p1'
        config.add_parameter(p1)

        p2 = script_configs.Parameter()
        p2.name = 'p2'
        config.add_parameter(p2)

        p3 = script_configs.Parameter()
        p3.name = 'p3'
        p3.param = '--p3'
        p3.no_value = True
        config.add_parameter(p3)

        p4 = script_configs.Parameter()
        p4.name = 'p4'
        p4.param = '-p4'
        config.add_parameter(p4)

        p5 = script_configs.Parameter()
        p5.name = 'p5'
        config.add_parameter(p5)

        args_string = executor.build_command_args({
            'p1': 'val1',
            'p2': 'val2',
            'p3': 'true',
            'p5': 'val5'},
            config)

        self.assertEqual(args_string, ['-p1', 'val1', 'val2', '--p3', 'val5'])

    def test_parameter_secure_no_value(self):
        config = script_configs.Config()
        config.script_command = 'ls'

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        config.add_parameter(parameter)

        executor = ScriptExecutor(config, {})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls', secure_command)

    def test_parameter_secure_some_value(self):
        config = script_configs.Config()
        config.script_command = 'ls'

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        config.add_parameter(parameter)

        executor = ScriptExecutor(config, {'p1': 'value'})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ******', secure_command)

    def test_parameter_secure_value_and_same_unsecure(self):
        config = script_configs.Config()
        config.script_command = 'ls'

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        config.add_parameter(parameter)

        parameter = script_configs.Parameter()
        parameter.name = 'p2'
        parameter.param = '-p2'
        config.add_parameter(parameter)

        executor = ScriptExecutor(config, {'p1': 'value', 'p2': 'value'})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ****** -p2 value', secure_command)

    def test_parameter_secure_multiselect(self):
        config = script_configs.Config()
        config.script_command = 'ls'

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        parameter.type = 'multiselect'
        config.add_parameter(parameter)

        executor = ScriptExecutor(config, {'p1': ['one', 'two', 'three']})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ******,******,******', secure_command)

    def test_parameter_secure_multiselect_as_multiarg(self):
        config = script_configs.Config()
        config.script_command = 'ls'

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        parameter.type = 'multiselect'
        parameter.multiple_arguments = True
        config.add_parameter(parameter)

        executor = ScriptExecutor(config, {'p1': ['one', 'two', 'three']})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ****** ****** ******', secure_command)


class TestProcessOutput(unittest.TestCase):
    def test_log_raw_single_line(self):
        self.create_and_start_executor()

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')

        wait_buffer_flush()

        self.assertEqual(['some text'], observer.data)

    def test_log_raw_single_buffer(self):
        self.create_and_start_executor()

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')
        self.write_process_output(' and continuation')

        wait_buffer_flush()

        self.assertEqual(['some text and continuation'], observer.data)

    def test_log_raw_multiple_buffers(self):
        self.create_and_start_executor()

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')

        wait_buffer_flush()

        self.write_process_output(' and continuation')

        wait_buffer_flush()

        self.assertEqual(['some text', ' and continuation'], observer.data)

    def test_log_with_secure(self):
        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.secure = True
        self.config.add_parameter(parameter)

        self.create_and_start_executor({'p1': 'a'})

        self.write_process_output('a| some text')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with some long long text |a')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, '******| some text\nand ****** new line with some long long text |******')

    def test_log_with_secure_ignore_whitespaces(self):
        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.secure = True
        self.config.add_parameter(parameter)

        self.create_and_start_executor({'p1': ' '})

        self.write_process_output('some text')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with some long long text')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, 'some text\nand a new line with some long long text')

    def test_log_with_secure_when_multiselect(self):
        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.secure = True
        parameter.type = 'multiselect'
        self.config.add_parameter(parameter)

        self.create_and_start_executor({'p1': ['123', 'password']})

        self.write_process_output('some text(123)')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with my password')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, 'some text(******)\nand a new line with my ******')

    def setUp(self):
        self.config = script_configs.Config()
        self.config.script_command = 'ls'
        executor._process_creator = _MockProcessWrapper

        super().setUp()

    def tearDown(self):
        super().tearDown()

        self.finish_process()
        self.executor.cleanup()

    def write_process_output(self, text):
        wrapper = self.executor.process_wrapper
        wrapper._write_script_output(text)

    # noinspection PyUnresolvedReferences
    def finish_process(self):
        self.executor.process_wrapper.kill()

    def get_finish_output(self):
        data = read_until_closed(self.executor.get_anonymized_output_stream(), timeout=BUFFER_FLUSH_WAIT_TIME)
        output = ''.join(data)
        return output

    def create_and_start_executor(self, parameter_values=None):
        if parameter_values is None:
            parameter_values = {}

        self.executor = ScriptExecutor(self.config, parameter_values)
        self.executor.start()
        return self.executor


def wait_buffer_flush():
    time.sleep(BUFFER_FLUSH_WAIT_TIME)
