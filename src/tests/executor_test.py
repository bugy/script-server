import time
import unittest

from execution import executor
from execution.executor import ScriptExecutor
from react.observable import _StoringObserver, read_until_closed
from tests import test_utils
from tests.test_utils import _MockProcessWrapper, create_config_model, create_script_param_config

BUFFER_FLUSH_WAIT_TIME = (executor.TIME_BUFFER_MS * 1.5) / 1000.0


class TestBuildCommandArgs(unittest.TestCase):
    def test_no_parameters_no_values(self):
        config = create_config_model('config_x')

        args_string = self.build_command_args({}, config)

        self.assertEqual([], args_string)

    def test_no_parameters_some_values(self):
        config = create_config_model('config_x')

        args_string = self.build_command_args({'p1': 'value', 'p2': 'value'}, config)

        self.assertEqual([], args_string)

    def test_one_parameter_no_values(self):
        config = create_config_model('config_x', parameters=[create_script_param_config('param1')])

        args_string = self.build_command_args({}, config)

        self.assertEqual([], args_string)

    def test_one_parameter_one_value(self):
        config = create_config_model('config_x', parameters=[create_script_param_config('p1')])

        args_string = self.build_command_args({'p1': 'value'}, config)

        self.assertEqual(['value'], args_string)

    def test_one_parameter_with_param(self):
        parameter = create_script_param_config('p1', param='-p1')
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': 'value'}, config)

        self.assertEqual(['-p1', 'value'], args_string)

    def test_one_parameter_flag_no_value(self):
        parameter = create_script_param_config('p1', param='--flag', no_value=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({}, config)

        self.assertEqual([], args_string)

    def test_one_parameter_flag_false(self):
        parameter = create_script_param_config('p1', param='--flag', no_value=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': False}, config)

        self.assertEqual([], args_string)

    def test_one_parameter_flag_true(self):
        parameter = create_script_param_config('p1', param='--flag', no_value=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': True}, config)

        self.assertEqual(['--flag'], args_string)

    def test_parameter_constant(self):
        parameter = create_script_param_config('p1', constant=True, default='const')
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': 'value'}, config)

        self.assertEqual(['const'], args_string)

    def test_parameter_int(self):
        parameter = create_script_param_config('p1', param='-p1', type='int')
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': 5}, config)

        self.assertEqual(['-p1', 5], args_string)

    def test_parameter_multiselect_when_empty_string(self):
        parameter = create_script_param_config('p1', param='-p1', type='multiselect')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ''}, config)

        self.assertEqual([], args_list)

    def test_parameter_multiselect_when_empty_list(self):
        parameter = create_script_param_config('p1', param='-p1', type='multiselect')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': []}, config)

        self.assertEqual([], args_list)

    def test_parameter_multiselect_when_single_list(self):
        parameter = create_script_param_config('p1', param='-p1', type='multiselect')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(['-p1', 'val1'], args_list)

    def test_parameter_multiselect_when_single_list_as_multiarg(self):
        parameter = create_script_param_config('p1', param='-p1', type='multiselect')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(['-p1', 'val1'], args_list)

    def test_parameter_multiselect_when_multiple_list(self):
        parameter = create_script_param_config('p1', type='multiselect')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1,val2,hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_and_custom_separator(self):
        parameter = create_script_param_config('p1', type='multiselect', multiselect_separator='; ')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1; val2; hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_as_multiarg(self):
        parameter = create_script_param_config('p1', type='multiselect', multiple_arguments=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1', 'val2', 'hello world'], args_list)

    def test_multiple_parameters_sequence(self):
        p1 = create_script_param_config('p1', param='-p1')
        p2 = create_script_param_config('p2')
        p3 = create_script_param_config('p3', param='--p3', no_value=True)
        p4 = create_script_param_config('p4', param='-p4')
        p5 = create_script_param_config('p5')
        config = create_config_model('config_x', parameters=[p1, p2, p3, p4, p5])

        args_string = self.build_command_args({
            'p1': 'val1',
            'p2': 'val2',
            'p3': 'true',
            'p5': 'val5'},
            config)

        self.assertEqual(args_string, ['-p1', 'val1', 'val2', '--p3', 'val5'])

    def test_parameter_secure_no_value(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True)
        config = create_config_model('config_x', config={'script_path': 'ls'}, parameters=[parameter])

        executor = ScriptExecutor(config, {})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls', secure_command)

    def test_parameter_secure_some_value(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True)
        config = create_config_model('config_x', config={'script_path': 'ls'}, parameters=[parameter])

        executor = ScriptExecutor(config, {'p1': 'value'})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ******', secure_command)

    def test_parameter_secure_value_and_same_unsecure(self):
        p1 = create_script_param_config('p1', param='-p1', secure=True)
        p2 = create_script_param_config('p2', param='-p2')
        config = create_config_model('config_x', config={'script_path': 'ls'}, parameters=[p1, p2])

        executor = ScriptExecutor(config, {'p1': 'value', 'p2': 'value'})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ****** -p2 value', secure_command)

    def test_parameter_secure_multiselect(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True, type='multiselect')
        config = create_config_model('config_x', config={'script_path': 'ls'}, parameters=[parameter])

        executor = ScriptExecutor(config, {'p1': ['one', 'two', 'three']})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ******', secure_command)

    def test_parameter_secure_multiselect_as_multiarg(self):
        parameter = create_script_param_config(
            'p1', param='-p1', secure=True, type='multiselect', multiple_arguments=True)
        config = create_config_model('config_x', config={'script_path': 'ls'}, parameters=[parameter])

        executor = ScriptExecutor(config, {'p1': ['one', 'two', 'three']})
        secure_command = executor.get_secure_command()

        self.assertEqual('ls -p1 ******', secure_command)

    def build_command_args(self, param_values, config):
        if config.script_command is None:
            config.script_command = 'ping'

        script_executor = ScriptExecutor(config, param_values)
        args_string = executor.build_command_args(script_executor.get_script_parameter_values(), config)
        return args_string


class TestProcessOutput(unittest.TestCase):
    def test_log_raw_single_line(self):
        config = self._create_config()
        self.create_and_start_executor(config)

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')

        wait_buffer_flush()

        self.assertEqual(['some text'], observer.data)

    def test_log_raw_single_buffer(self):
        config = self._create_config()
        self.create_and_start_executor(config)

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')
        self.write_process_output(' and continuation')

        wait_buffer_flush()

        self.assertEqual(['some text and continuation'], observer.data)

    def test_log_raw_multiple_buffers(self):
        config = self._create_config()
        self.create_and_start_executor(config)

        observer = _StoringObserver()
        self.executor.get_raw_output_stream().subscribe(observer)

        self.write_process_output('some text')

        wait_buffer_flush()

        self.write_process_output(' and continuation')

        wait_buffer_flush()

        self.assertEqual(['some text', ' and continuation'], observer.data)

    def test_log_with_secure(self):
        parameter = create_script_param_config('p1', secure=True)
        config = self._create_config(parameters=[parameter])

        self.create_and_start_executor(config, {'p1': 'a'})

        self.write_process_output('a| some text')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with some long long text |a')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, '******| some text\nand ****** new line with some long long text |******')

    def test_log_with_secure_ignore_whitespaces(self):
        parameter = create_script_param_config('p1', secure=True)
        config = self._create_config(parameters=[parameter])

        self.create_and_start_executor(config, {'p1': ' '})

        self.write_process_output('some text')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with some long long text')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, 'some text\nand a new line with some long long text')

    def test_log_with_secure_ignore_inside_word(self):
        parameter = create_script_param_config('p1', secure=True)
        config = self._create_config(parameters=[parameter])

        self.create_and_start_executor(config, {'p1': 'cat'})

        self.write_process_output('cat\n-cat-\nbobcat\ncatty\n1cat\nmy cat is cute')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, '******\n-******-\nbobcat\ncatty\n1cat\nmy ****** is cute')

    def test_log_with_secure_when_multiselect(self):
        parameter = create_script_param_config('p1', secure=True, type='multiselect')
        config = self._create_config(parameters=[parameter])

        self.create_and_start_executor(config, {'p1': ['123', 'password']})

        self.write_process_output('some text(123)')
        self.write_process_output('\nand a new line')
        self.write_process_output(' with my password')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, 'some text(******)\nand a new line with my ******')

    def test_log_with_secure_when_with_symbols(self):
        parameter = create_script_param_config('p1', secure=True)
        config = self._create_config(parameters=[parameter])

        value = '/some.text?#&^and_=+chars\\'
        self.create_and_start_executor(config, {'p1': value})

        self.write_process_output('Writing ' + value + '\n')
        self.write_process_output('...\n')
        self.write_process_output(value + '-')
        self.write_process_output('\nDone')

        self.finish_process()

        output = self.get_finish_output()
        self.assertEqual(output, 'Writing ******\n...\n******-\nDone')

    @staticmethod
    def _create_config(parameters=None):
        return create_config_model('config_x', config={'script_path': 'ls'}, parameters=parameters)

    def setUp(self):
        self.config = create_config_model('config_x')
        self.config.script_command = 'ls'
        executor._process_creator = _MockProcessWrapper

        test_utils.setup()

        super().setUp()

    def tearDown(self):
        super().tearDown()

        test_utils.cleanup()

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

    def create_and_start_executor(self, config, parameter_values=None):
        if parameter_values is None:
            parameter_values = {}

        self.executor = ScriptExecutor(config, parameter_values)
        self.executor.start()
        return self.executor


def wait_buffer_flush():
    time.sleep(BUFFER_FLUSH_WAIT_TIME)
