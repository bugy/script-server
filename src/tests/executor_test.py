import os
import time
import unittest

from config.constants import PARAM_TYPE_MULTISELECT
from execution import executor
from execution.executor import ScriptExecutor, _build_env_variables, create_process_wrapper
from react.observable import _StoringObserver, read_until_closed
from tests import test_utils
from tests.test_utils import _MockProcessWrapper, create_config_model, create_script_param_config, \
    create_parameter_model, assert_contains_sub_dict

BUFFER_FLUSH_WAIT_TIME = (executor.TIME_BUFFER_MS * 1.5) / 1000.0


def parse_env_variables(output):
    lines = [line for line in output.split('\n') if line and ('=' in line)]
    variables = {line.split('=', 2)[0]: line.split('=', 2)[1] for line in lines}
    return variables


class TestScriptExecutor(unittest.TestCase):
    def test_start_without_values(self):
        self.create_executor(create_config_model('config_x'), {})
        self.executor.start(123)

        process_wrapper = self.executor.process_wrapper
        self.assertEqual(None, process_wrapper.working_directory)
        self.assertEqual(['ls'], process_wrapper.command)

        expected_values = {}
        expected_values.update(os.environ)
        expected_values['EXECUTION_ID'] = '123'
        self.assertEqual(expected_values, process_wrapper.all_env_variables)

    def test_start_with_one_value(self):
        config = create_config_model('config_x', parameters=[create_script_param_config('id')])
        self.create_executor(config, {'id': 918273})
        self.executor.start(123)

        process_wrapper = self.executor.process_wrapper
        self.assertEqual(['ls', 918273], process_wrapper.command)
        assert_contains_sub_dict(self,
                                 process_wrapper.all_env_variables,
                                 {'PARAM_ID': '918273', 'EXECUTION_ID': '123'})

    def test_start_with_multiple_values(self):
        config = create_config_model('config_x', parameters=[
            create_script_param_config('id'),
            create_script_param_config('name', env_var='My_Name', param='-n'),
            create_script_param_config('verbose', param='--verbose', no_value=True),
        ])
        self.create_executor(config, {'id': 918273, 'name': 'UserX', 'verbose': True})
        self.executor.start(123)

        process_wrapper = self.executor.process_wrapper
        self.assertEqual(['ls', 918273, '-n', 'UserX', '--verbose'], process_wrapper.command)
        assert_contains_sub_dict(self,
                                 process_wrapper.all_env_variables,
                                 {'PARAM_ID': '918273',
                                  'My_Name': 'UserX',
                                  'PARAM_VERBOSE': 'true',
                                  'EXECUTION_ID': '123'})

    def test_env_variables_when_pty(self):
        with test_utils.custom_env('some_env', 'test'):
            config = create_config_model(
                'config_x',
                script_command='tests/scripts/printenv.sh',
                requires_terminal=True,
                parameters=[
                    create_script_param_config('id'),
                    create_script_param_config('name', env_var='My_Name', param='-n'),
                    create_script_param_config('verbose', param='--verbose', no_value=True),
                ])

            executor._process_creator = create_process_wrapper
            self.create_executor(config, {'id': '918273', 'name': 'UserX', 'verbose': True})
            self.executor.start(123)

            data = read_until_closed(self.executor.get_raw_output_stream(), 100)
            output = ''.join(data)

            variables = parse_env_variables(output)
            self.assertEqual('918273', variables.get('PARAM_ID'))
            self.assertEqual('UserX', variables.get('My_Name'))
            self.assertEqual('true', variables.get('PARAM_VERBOSE'))
            self.assertEqual('test', variables.get('some_env'))
            self.assertEqual('123', variables.get('EXECUTION_ID'))

    def test_env_variables_when_popen(self):
        with test_utils.custom_env('some_env', 'test'):
            config = create_config_model(
                'config_x',
                script_command='tests/scripts/printenv.sh',
                requires_terminal=False,
                parameters=[
                    create_script_param_config('id'),
                    create_script_param_config('name', env_var='My_Name', param='-n'),
                    create_script_param_config('verbose', param='--verbose', no_value=True),
                ])

            executor._process_creator = create_process_wrapper
            self.create_executor(config, {'id': '918273', 'name': 'UserX', 'verbose': True})
            self.executor.start(123)

            data = read_until_closed(self.executor.get_raw_output_stream(), 100)
            output = ''.join(data)

            variables = parse_env_variables(output)
            self.assertEqual('918273', variables.get('PARAM_ID'))
            self.assertEqual('UserX', variables.get('My_Name'))
            self.assertEqual('true', variables.get('PARAM_VERBOSE'))
            self.assertEqual('test', variables.get('some_env'))
            self.assertEqual('123', variables.get('EXECUTION_ID'))

    def test_start_with_multiple_values_when_one_not_exist(self):
        config = create_config_model('config_x', parameters=[
            create_script_param_config('id'),
            create_script_param_config('verbose', param='--verbose', no_value=True),
        ])
        self.create_executor(config, {'id': 918273, 'name': 'UserX', 'verbose': True})
        self.executor.start(123)

        process_wrapper = self.executor.process_wrapper
        self.assertEqual(['ls', 918273, '--verbose'], process_wrapper.command)
        assert_contains_sub_dict(self,
                                 process_wrapper.all_env_variables,
                                 {'PARAM_ID': '918273', 'PARAM_VERBOSE': 'true', 'EXECUTION_ID': '123'})

    def create_executor(self, config, parameter_values):
        self.executor = ScriptExecutor(config, parameter_values, test_utils.env_variables)

    def setUp(self):
        executor._process_creator = _MockProcessWrapper
        test_utils.setup()

    def tearDown(self) -> None:
        self.executor.process_wrapper.kill()

        test_utils.cleanup()


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
        parameter = create_script_param_config('p1', param='-p1', type=PARAM_TYPE_MULTISELECT)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ''}, config)

        self.assertEqual([], args_list)

    def test_parameter_multiselect_when_empty_list(self):
        parameter = create_script_param_config('p1', param='-p1', type=PARAM_TYPE_MULTISELECT)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': []}, config)

        self.assertEqual([], args_list)

    def test_parameter_multiselect_when_single_list(self):
        parameter = create_script_param_config('p1', param='-p1', type=PARAM_TYPE_MULTISELECT)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(['-p1', 'val1'], args_list)

    def test_parameter_multiselect_when_single_list_as_multiarg(self):
        parameter = create_script_param_config('p1', param='-p1', type=PARAM_TYPE_MULTISELECT)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1']}, config)

        self.assertEqual(['-p1', 'val1'], args_list)

    def test_parameter_multiselect_when_multiple_list(self):
        parameter = create_script_param_config('p1', type=PARAM_TYPE_MULTISELECT)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1,val2,hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_and_custom_separator(self):
        parameter = create_script_param_config('p1', type=PARAM_TYPE_MULTISELECT, multiselect_separator='; ')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1; val2; hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_as_multiarg(self):
        parameter = create_script_param_config('p1',
                                               type=PARAM_TYPE_MULTISELECT,
                                               multiselect_argument_type='argument_per_value')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['val1', 'val2', 'hello world'], args_list)

    def test_parameter_without_space(self):
        parameter = create_script_param_config('p1', param='-p1=', same_arg_param=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': "value"}, config)

        self.assertEqual(['-p1=value'], args_string)

    def test_parameter_int_without_space(self):
        parameter = create_script_param_config('p1', param='-p1=', type='int', same_arg_param=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_string = self.build_command_args({'p1': 10}, config)

        self.assertEqual(['-p1=10'], args_string)

    def test_parameter_multiselect_when_multiple_list_without_space(self):
        parameter = create_script_param_config('p1', param='--p1=', type=PARAM_TYPE_MULTISELECT, same_arg_param=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['--p1=val1,val2,hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_and_argument_per_value_without_space(self):
        parameter = create_script_param_config('p1', param='--p1=',
                                               type=PARAM_TYPE_MULTISELECT,
                                               multiselect_argument_type='argument_per_value',
                                               same_arg_param=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['--p1=val1', 'val2', 'hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_as_multiarg_repeat_param(self):
        parameter = create_script_param_config('p1', param='-p1',
                                               type=PARAM_TYPE_MULTISELECT,
                                               multiselect_argument_type='repeat_param_value')
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['-p1', 'val1', '-p1', 'val2', '-p1', 'hello world'], args_list)

    def test_parameter_multiselect_when_multiple_list_as_multiarg_repeat_param_without_space(self):
        parameter = create_script_param_config('p1', param='--p1=',
                                               type=PARAM_TYPE_MULTISELECT,
                                               multiselect_argument_type='repeat_param_value',
                                               same_arg_param=True)
        config = create_config_model('config_x', parameters=[parameter])

        args_list = self.build_command_args({'p1': ['val1', 'val2', 'hello world']}, config)

        self.assertEqual(['--p1=val1', '--p1=val2', '--p1=hello world'], args_list)

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

    def build_command_args(self, param_values, config):
        if config.script_command is None:
            config.script_command = 'ping'

        script_executor = ScriptExecutor(config, param_values, test_utils.env_variables)
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
        parameter = create_script_param_config('p1', secure=True, type=PARAM_TYPE_MULTISELECT)
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
        return create_config_model('config_x', parameters=parameters)

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

        self.executor = ScriptExecutor(config, parameter_values, test_utils.env_variables)
        self.executor.start(123)
        return self.executor


class GetSecureCommandTest(unittest.TestCase):
    def test_secure_value_not_specified(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True)
        secure_command = self.get_secure_command([parameter], {})

        self.assertEqual('ls', secure_command)

    def test_some_secure_value(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True)
        secure_command = self.get_secure_command([parameter], {'p1': 'value'})

        self.assertEqual('ls -p1 ******', secure_command)

    def test_parameter_secure_value_and_same_unsecure(self):
        p1 = create_script_param_config('p1', param='-p1', secure=True)
        p2 = create_script_param_config('p2', param='-p2')

        secure_command = self.get_secure_command([p1, p2], {'p1': 'value', 'p2': 'value'})

        self.assertEqual('ls -p1 ****** -p2 value', secure_command)

    def test_parameter_secure_multiselect(self):
        parameter = create_script_param_config('p1', param='-p1', secure=True, type=PARAM_TYPE_MULTISELECT)

        secure_command = self.get_secure_command([parameter], {'p1': ['one', 'two', 'three']})

        self.assertEqual('ls -p1 ******', secure_command)

    def test_parameter_secure_multiselect_as_multiarg(self):
        parameter = create_script_param_config(
            'p1', param='-p1', secure=True, type=PARAM_TYPE_MULTISELECT, multiselect_argument_type='argument_per_value')

        secure_command = self.get_secure_command([parameter], {'p1': ['one', 'two', 'three']})

        self.assertEqual('ls -p1 ****** ****** ******', secure_command)

    def test_parameter_no_value(self):
        parameter = create_script_param_config(
            'p1', param='-p1', no_value=True)

        secure_command = self.get_secure_command([parameter], {'p1': True})

        self.assertEqual('ls -p1', secure_command)

    def test_parameter_multiselect_and_argument_per_value(self):
        parameter = create_script_param_config(
            'p1', param='-p1', type=PARAM_TYPE_MULTISELECT, multiselect_argument_type='argument_per_value')

        secure_command = self.get_secure_command([parameter], {'p1': ['abc', 'def']})

        self.assertEqual('ls -p1 abc def', secure_command)

    def test_when_parameter_multiselect_and_comma_separated(self):
        parameter = create_script_param_config(
            'p1', param='-p1', type=PARAM_TYPE_MULTISELECT)

        secure_command = self.get_secure_command([parameter], {'p1': ['abc', 'def']})

        self.assertEqual('ls -p1 abc,def', secure_command)

    def test_secure_parameter_no_value(self):
        parameter = create_script_param_config(
            'p1', param='-p1', no_value=True, secure=True)
        secure_command = self.get_secure_command([parameter], {'p1': True})

        self.assertEqual('ls -p1', secure_command)

    def test_parameter_int(self):
        parameter = create_script_param_config(
            'p1', param='-p1', type='int')

        secure_command = self.get_secure_command([parameter], {'p1': 123})

        self.assertEqual('ls -p1 123', secure_command)

    def test_secure_parameter_int(self):
        parameter = create_script_param_config(
            'p1', param='-p1', type='int', secure=True)

        secure_command = self.get_secure_command([parameter], {'p1': 123})

        self.assertEqual('ls -p1 ******', secure_command)

    def get_secure_command(self, parameters, values):
        config = create_config_model('config_x', parameters=parameters)
        executor = ScriptExecutor(config, values, test_utils.env_variables)
        return executor.get_secure_command()


class TestBuildEnvVariables(unittest.TestCase):
    def test_single_variable(self):
        param = create_parameter_model('name')
        env_variables = _build_env_variables({'name': 'UserX'}, [param], 123)

        self.assertEqual({'PARAM_NAME': 'UserX', 'EXECUTION_ID': '123'}, env_variables)

    def test_multiple_variables(self):
        name_param = create_parameter_model('name')
        id_param = create_parameter_model('id')
        address_param = create_parameter_model('address')
        env_variables = _build_env_variables(
            {'name': 'UserX', 'id': 918273, 'address': 'Germany'},
            [name_param, id_param, address_param],
            123)

        self.assertEqual({'PARAM_NAME': 'UserX',
                          'PARAM_ID': '918273',
                          'PARAM_ADDRESS': 'Germany',
                          'EXECUTION_ID': '123'},
                         env_variables)

    def test_missing_parameter(self):
        name_param = create_parameter_model('name')
        env_variables = _build_env_variables(
            {'name': 'UserX', 'id': 918273},
            [name_param],
            123)

        self.assertEqual({'PARAM_NAME': 'UserX', 'EXECUTION_ID': '123'}, env_variables)

    def test_missing_value(self):
        id_param = create_parameter_model('id')
        name_param = create_parameter_model('name')
        env_variables = _build_env_variables(
            {'name': None, 'id': 918273},
            [name_param, id_param],
            123)

        self.assertEqual({'PARAM_ID': '918273', 'EXECUTION_ID': '123'}, env_variables)

    def test_list_value(self):
        id_param = create_parameter_model('id')
        name_param = create_parameter_model('name')
        env_variables = _build_env_variables(
            {'name': ['Peter', 'Schwarz'], 'id': 918273},
            [name_param, id_param],
            123)

        self.assertEqual({'PARAM_ID': '918273', 'EXECUTION_ID': '123'}, env_variables)

    def test_boolean_value(self):
        verbose_param = create_parameter_model('verbose')
        env_variables = _build_env_variables({'verbose': True}, [verbose_param], 123)

        self.assertEqual({'PARAM_VERBOSE': 'True', 'EXECUTION_ID': '123'}, env_variables)

    def test_boolean_value_when_false(self):
        verbose_param = create_parameter_model('verbose')
        env_variables = _build_env_variables({'verbose': False}, [verbose_param], 123)

        self.assertEqual({'PARAM_VERBOSE': 'False', 'EXECUTION_ID': '123'}, env_variables)

    def test_boolean_value_when_no_value(self):
        verbose_param = create_parameter_model('verbose', no_value=True)
        env_variables = _build_env_variables({'verbose': True}, [verbose_param], 123)

        self.assertEqual({'PARAM_VERBOSE': 'true', 'EXECUTION_ID': '123'}, env_variables)

    def test_boolean_value_when_no_value_and_false(self):
        verbose_param = create_parameter_model('verbose', no_value=True)
        env_variables = _build_env_variables({'verbose': False}, [verbose_param], 123)

        self.assertEqual({'EXECUTION_ID': '123'}, env_variables)

    def test_explicit_env_var(self):
        name_param = create_parameter_model('name', env_var='My_Name')
        env_variables = _build_env_variables({'name': 'UserX'}, [name_param], 123)

        self.assertEqual({'My_Name': 'UserX', 'EXECUTION_ID': '123'}, env_variables)

    def test_replace_characters(self):
        name_param = create_parameter_model('Мой параметер 1!')
        env_variables = _build_env_variables({'Мой параметер 1!': 'UserX'}, [name_param], 123)

        self.assertEqual({'PARAM_MOY_PARAMETER_1_': 'UserX', 'EXECUTION_ID': '123'}, env_variables)

    def test_replace_squash_underscores(self):
        name_param = create_parameter_model('hello !@#$%^& world')
        env_variables = _build_env_variables({'hello !@#$%^& world': 'UserX'}, [name_param], 123)

        self.assertEqual({'PARAM_HELLO_WORLD': 'UserX', 'EXECUTION_ID': '123'}, env_variables)

    def test_replace_when_no_valid_characters(self):
        name_param = create_parameter_model(' !@#$%^&')
        env_variables = _build_env_variables({' !@#$%^&': 'UserX'}, [name_param], 123)

        self.assertEqual({'EXECUTION_ID': '123'}, env_variables)

    def test_conflicting_name(self):
        param1 = create_parameter_model('A+')
        param2 = create_parameter_model('A-')
        param3 = create_parameter_model('A=')
        param4 = create_parameter_model('A')
        env_variables = _build_env_variables({'A+': 'x', 'A-': 'y', 'A=': 'z', 'A': 'a'},
                                             [param1, param2, param3, param4],
                                             123)

        self.assertEqual({'PARAM_A': 'a', 'EXECUTION_ID': '123'}, env_variables)

    def test_conflicting_name_when_explicit(self):
        param1 = create_parameter_model('A+')
        param2 = create_parameter_model('A-', env_var='B')
        param3 = create_parameter_model('A=')
        param4 = create_parameter_model('A')
        env_variables = _build_env_variables({'A+': 'x', 'A-': 'y', 'A=': 'z', 'A': 'a'},
                                             [param1, param2, param3, param4],
                                             123)

        self.assertEqual({'PARAM_A': 'a', 'B': 'y', 'EXECUTION_ID': '123'}, env_variables)

    def test_conflicting_name_when_execution_id(self):
        param = create_parameter_model('p1', env_var='EXECUTION_ID')
        env_variables = _build_env_variables({'p1': 'x'}, [param], 123)

        self.assertEqual({'EXECUTION_ID': 'x'}, env_variables)


def wait_buffer_flush():
    time.sleep(BUFFER_FLUSH_WAIT_TIME)
