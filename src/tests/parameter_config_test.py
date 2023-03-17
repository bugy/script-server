import inspect
import os
import unittest
from collections import OrderedDict

from parameterized import parameterized

from config.constants import PARAM_TYPE_SERVER_FILE, PARAM_TYPE_MULTISELECT
from model import parameter_config
from model.parameter_config import get_sorted_config
from react.properties import ObservableDict, ObservableList
from tests import test_utils
from tests.test_utils import create_parameter_model, create_parameter_model_from_config
from utils.process_utils import ExecutionException
from utils.string_utils import is_blank

DEF_USERNAME = 'my_user'
DEF_AUDIT_NAME = 'my_user-pc'


class ParameterModelInitTest(unittest.TestCase):
    def test_create_empty_parameter(self):
        parameter_model = create_parameter_model('param1')
        self.assertEqual('param1', parameter_model.name)

    def test_create_full_parameter(self):
        name = 'full_param'
        param = '-f'
        description = 'Full parameter description'
        required = True
        min = 5
        max = 13
        separator = '|'
        default = '8'
        type = 'list'
        values = ['val1', 'val2', 'val3']

        parameter_model = _create_parameter_model({
            'name': name,
            'param': param,
            'env_var': 'my_Param',
            'no_value': 'true',
            'description': description,
            'required': required,
            'min': min,
            'max': max,
            'separator': separator,
            'multiselect_argument_type': 'argument_per_value',
            'default': default,
            'type': type,
            'constant': 'false',
            'values': values,
            'ui': {
                'width_weight': '3'
            }
        })

        self.assertEqual(name, parameter_model.name)
        self.assertEqual(param, parameter_model.param)
        self.assertEqual('my_Param', parameter_model.env_var)
        self.assertEqual(True, parameter_model.no_value)
        self.assertEqual(description, parameter_model.description)
        self.assertEqual(required, parameter_model.required)
        self.assertEqual(min, parameter_model.min)
        self.assertEqual(max, parameter_model.max)
        self.assertEqual(separator, parameter_model.separator)
        self.assertEqual('argument_per_value', parameter_model.multiselect_argument_type)
        self.assertEqual(default, parameter_model.default)
        self.assertEqual(type, parameter_model.type)
        self.assertEqual(False, parameter_model.constant)
        self.assertEqual(3, parameter_model.ui_width_weight)
        self.assertCountEqual(values, parameter_model.values)

    def test_default_settings(self):
        parameter_model = create_parameter_model('param_with_defaults')
        self.assertEqual('param_with_defaults', parameter_model.name)
        self.assertEqual(False, parameter_model.no_value)
        self.assertEqual(False, parameter_model.required)
        self.assertEqual(False, parameter_model.secure)
        self.assertEqual(',', parameter_model.separator)
        self.assertEqual('text', parameter_model.type)
        self.assertEqual(False, parameter_model.constant)
        self.assertEqual(None, parameter_model.ui_width_weight)

    def test_default_value_from_env(self):
        test_utils.set_os_environ_value('my_env_var', 'sky')

        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'default': '$$my_env_var'})
        self.assertEqual('sky', parameter_model.default)

    def test_default_value_from_env_when_missing(self):
        test_utils.set_os_environ_value('my_env_var', 'earth')

        self.assertRaisesRegex(
            Exception,
            'Environment variable my_env_var2 is not set',
            _create_parameter_model,
            {'name': 'def_param', 'default': '$$my_env_var2'})

    def test_default_value_from_auth(self):
        parameter_model = _create_parameter_model({'name': 'def_param', 'default': 'X${auth.username}X'})
        self.assertEqual('X' + DEF_USERNAME + 'X', parameter_model.default)

    def test_prohibit_constant_without_default(self):
        self.assertRaisesRegex(Exception, 'Constant should have default value specified',
                               _create_parameter_model, {'name': 'def_param', 'constant': 'true'})

    def test_prohibit_constant_without_default_and_name(self):
        self.assertRaisesRegex(Exception, 'Constant should have default value specified',
                               _create_parameter_model, {'constant': 'true'})

    def test_values_from_script(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'list',
            'values': {'script': 'echo "123\n" "456"'}})
        self.assertEqual(['123', ' 456'], parameter_model.values)

    @parameterized.expand([
        ('y2', None, ['y2', 'y3']),
        ('y2', False, ['x1', 'y2', 'y3 | grep y']),
        ('y2', True, ['y2', 'y3']),
        ('${auth.username}', None, ['x1', 'my_user', 'y3 | grep y']),
        ('${auth.username}', False, ['x1', 'my_user', 'y3 | grep y']),
        ('${auth.username}', True, ['my_user', 'y3']),
    ])
    def test_values_from_script_with_bash_operator(self, second_value, shell, expected_values):
        values = {'script': 'echo "x1\n""%s\n""y3" | grep y' % (second_value,)}
        if shell is not None:
            values['shell'] = shell

        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'list',
            'values': values})
        self.assertEqual(expected_values, parameter_model.values)

    def test_values_from_script_win_newline(self):
        test_utils.set_win()

        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'list',
            'values': {'script': 'echo "123\r\n" "456"'}})
        self.assertEqual(['123', ' 456'], parameter_model.values)

    def test_allowed_values_for_non_list(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'int',
            'values': {'script': 'echo "123\n" "456"'}})
        self.assertEqual(None, parameter_model.values)

    def test_allowed_values_for_editable_list(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'editable_list',
            'values': {'script': 'echo "123\n" "456"'}})
        self.assertEqual(['123', ' 456'], parameter_model.values)

    def test_ip_uppercase(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'IP'})
        self.assertEqual('ip', parameter_model.type)

    def test_ip_with_v(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'Ipv6'})
        self.assertEqual('ip6', parameter_model.type)

    def test_multiline_text(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'multiline_text'})
        self.assertEqual('multiline_text', parameter_model.type)

    def tearDown(self):
        super().tearDown()

        test_utils.cleanup()


class ParameterModelMapValueTest(unittest.TestCase):
    def test_map_to_script_simple_value(self):
        parameter_model = create_parameter_model('param1')
        self.assertEqual('abc', parameter_model.map_to_script('abc'))

    def test_map_to_script_file_value(self):
        file_dir = os.path.expanduser('~')
        parameter_model = create_parameter_model('param1', type=PARAM_TYPE_SERVER_FILE,
                                                 file_dir=file_dir)

        mapped_value = parameter_model.map_to_script('abc')
        self.assertEqual(os.path.join(file_dir, 'abc'), mapped_value)

    def test_map_to_script_multiselect(self):
        parameter_model = create_parameter_model('param1', type=PARAM_TYPE_MULTISELECT,
                                                 allowed_values=['abc', 'def', '456'])
        self.assertEqual(['456', 'def'], parameter_model.map_to_script(['456', 'def']))

    def test_map_to_script_args_single(self):
        parameter_model = create_parameter_model('param1')
        self.assertEqual('hello', parameter_model.to_script_args('hello'))

    def test_map_to_script_args_multiselect_list(self):
        parameter_model = create_parameter_model('param1',
                                                 type=PARAM_TYPE_MULTISELECT,
                                                 allowed_values=['abc', 'def', '456'],
                                                 multiselect_argument_type='argument_per_value')
        self.assertEqual(['abc', '456'], parameter_model.to_script_args(['abc', '456']))

    def test_map_to_script_args_multiselect_single_arg(self):
        parameter_model = create_parameter_model('param1',
                                                 type=PARAM_TYPE_MULTISELECT,
                                                 allowed_values=['abc', 'def', '456'],
                                                 multiselect_separator='_')
        self.assertEqual('abc_456_def', parameter_model.to_script_args(['abc', '456', 'def']))


class TestDefaultValue(unittest.TestCase):

    def test_no_value(self):
        default = self.resolve_default(None)

        self.assertEqual(default, None)

    def test_empty_value(self):
        default = self.resolve_default('')

        self.assertEqual(default, '')

    def test_text_value(self):
        default = self.resolve_default('text')

        self.assertEqual(default, 'text')

    def test_unicode_value(self):
        default = self.resolve_default(u'text')

        self.assertEqual(default, u'text')

    def test_int_value(self):
        default = self.resolve_default(5)

        self.assertEqual(default, 5)

    def test_bool_value(self):
        default = self.resolve_default(True)

        self.assertEqual(default, True)

    def test_env_variable(self):
        test_utils.set_os_environ_value('test_val', 'text')

        default = self.resolve_default('$$test_val')

        self.assertEqual(default, 'text')

    def test_missing_env_variable(self):
        self.assertRaises(Exception, self.resolve_default, '$$test_val')

    def test_auth_username(self):
        default = self.resolve_default('${auth.username}', username='buggy')
        self.assertEqual('buggy', default)

    def test_auth_username_when_none(self):
        default = self.resolve_default('${auth.username}')
        self.assertEqual('', default)

    def test_auth_username_when_inside_text(self):
        default = self.resolve_default('__${auth.username}__', username='usx')
        self.assertEqual('__usx__', default)

    def test_auth_audit_name(self):
        default = self.resolve_default('${auth.audit_name}', audit_name='127.0.0.1')
        self.assertEqual('127.0.0.1', default)

    def test_auth_audit_name_when_none(self):
        default = self.resolve_default('${auth.audit_name}')
        self.assertEqual('', default)

    def test_auth_audit_name_when_inside_text(self):
        default = self.resolve_default('__${auth.audit_name}__', audit_name='usx')
        self.assertEqual('__usx__', default)

    def test_auth_username_and_audit_name(self):
        default = self.resolve_default('${auth.username}:${auth.audit_name}', username='buggy', audit_name='localhost')
        self.assertEqual('buggy:localhost', default)

    def test_script_value(self):
        default = self.resolve_default({'script': 'echo 123'})
        self.assertEqual('123', default)

    def test_script_value_with_working_dir(self):
        default = self.resolve_default({'script': 'pwd'}, working_dir=test_utils.temp_folder)
        abs_temp_path = os.path.abspath(test_utils.temp_folder)
        self.assertEqual(abs_temp_path, default)

    def test_script_value_when_env_var(self):
        test_utils.set_os_environ_value('my_command', 'echo "Hello world"')

        default = self.resolve_default({'script': '$$my_command'}, working_dir=test_utils.temp_folder)
        self.assertEqual('Hello world', default)

    def test_script_value_when_username(self):
        default = self.resolve_default({'script': 'echo "x${auth.username}x"'},
                                       working_dir=test_utils.temp_folder,
                                       username='TONY')
        self.assertEqual('xTONYx', default)

    @parameterized.expand([
        ('y', None, 'my_user\ny1'),
        ('y', False, ExecutionException),
        ('y', True, 'my_user\ny1'),
        ('${auth.username}', None, 'my_user'),
        ('${auth.username}', False, ExecutionException),
        ('${auth.username}', True, 'my_user'),
    ])
    def test_script_value_with_shell_operators(self, grep_pattern, shell, expected_value):
        test_utils.create_files(['x1', 'y1', 'my_user'])
        config = {'script': 'ls "%s" | grep %s' % (test_utils.temp_folder, grep_pattern)}
        if shell is not None:
            config['shell'] = shell

        if inspect.isclass(expected_value) and issubclass(expected_value, BaseException):
            self.assertRaises(expected_value, self.resolve_default, config, username='my_user')
        else:
            default = self.resolve_default(config, username='my_user')
            self.assertEqual(expected_value, default)

    @parameterized.expand([
        ('multiselect', '123', '123'),
        ('list', '123', '123'),
        ('multiselect', '123\n', '123'),
        ('multiselect', '123\n456', ['123', '456']),
        ('list', '123\n456', '123\n456'),
        ('multiselect', '\n123\n456\n', ['123', '456']),
        ('multiselect', '\n123 \n \t 456\n', ['123', '456']),
        ('multiselect', '123 \n \t 456\n789', ['123', '456', '789']),
    ])
    def test_script_value_when_multiselect_and_multiple_values(self, type, output, expected_value):
        config = {'script': 'echo "' + output + '"'}

        default = self.resolve_default(config, username='my_user', type=type)
        self.assertEqual(expected_value, default)

    @parameterized.expand([
        ('echo ${param1}', {'param1': 'xyz'}, 'xyz'),
        ('echo ${param1}', {'param2': 'abc'}, None),
        ('echo ${param1}', {}, None),
        ('echo "${auth.username}-${param2}"', {'param1': 'xyz'}, None),
        ('echo "${auth.username}-${param2}"', {'param2': 'abc'}, 'my_user-abc'),
        ('echo "${param1}-${param2}"', {'param1': 'xyz', 'param2': 'abc'}, 'xyz-abc'),
        ('echo "${param1}-${param2}"', {'param1': 'xyz'}, None),
        ('echo "${param1}-${param2}"', {'param2': 'abc'}, None),
        ('echo "${param3}"', {}, None),
    ])
    def test_script_value_when_dynamic_script(self, script, values, expected_value):
        parameters = ObservableList([
            _create_parameter_model({'name': 'param1'}),
            _create_parameter_model({'name': 'param2'})])

        parameter_values = ObservableDict()

        parameter_model = self.prepare_parameter_model(
            {'script': script},
            username='my_user',
            other_parameters=parameters,
            parameter_values=parameter_values
        )

        self.assertEqual(None, parameter_model.default)

        for (key, value) in values.items():
            parameter_values[key] = value

        self.assertEqual(expected_value, parameter_model.default)

    def test_script_value_when_dynamic_script_value_change_to_null(self):
        parameters = ObservableList([_create_parameter_model({'name': 'param1'})])

        parameter_values = ObservableDict({'param1': 'abc'})

        parameter_model = self.prepare_parameter_model(
            {'script': 'echo ${param1}'},
            username='my_user',
            other_parameters=parameters,
            parameter_values=parameter_values
        )

        self.assertEqual('abc', parameter_model.default)

        parameter_values['param1'] = None

        self.assertEqual(None, parameter_model.default)

    def test_script_value_when_dynamic_script_shell_true(self):
        parameters = ObservableList([_create_parameter_model({'name': 'param1'})])

        parameter_values = ObservableDict()

        parameter_model = self.prepare_parameter_model(
            {'script': 'echo "${param1}" | grep a', 'shell': True},
            other_parameters=parameters,
            parameter_values=parameter_values
        )

        parameter_values['param1'] = 'abc\ndef\ncat'

        self.assertEqual('abc\ncat', parameter_model.default)

    @parameterized.expand([
        (False,),
        (None,),
    ])
    def test_script_value_when_dynamic_script_shell_false(self, shell):
        parameters = ObservableList([_create_parameter_model({'name': 'param1'})])

        parameter_values = ObservableDict()

        parameter_model = self.prepare_parameter_model(
            {'script': 'echo "${param1}" | grep a', 'shell': shell},
            other_parameters=parameters,
            parameter_values=parameter_values
        )

        parameter_values['param1'] = 'abc\ndef\ncat'

        self.assertEqual('abc\ndef\ncat | grep a', parameter_model.default)

    @staticmethod
    def resolve_default(value, *, username=None, audit_name=None, working_dir=None, type=None):
        model = TestDefaultValue.prepare_parameter_model(
            value,
            username=username,
            audit_name=audit_name,
            working_dir=working_dir,
            type=type)

        return model.default

    @staticmethod
    def prepare_parameter_model(
            value,
            *,
            username=None,
            audit_name=None,
            working_dir=None,
            type=None,
            other_parameters=None,
            parameter_values=None):

        config = {
            'name': 'some param',
            'default': value
        }

        if type is not None:
            config['type'] = type

        if parameter_values is None:
            parameter_values = ObservableDict()

        if other_parameters is None:
            other_parameters = ObservableList()

        return parameter_config.ParameterModel(
            config,
            username,
            audit_name,
            lambda: other_parameters,
            test_utils.process_invoker,
            other_param_values=parameter_values,
            working_dir=working_dir)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestSingleParameterValidation(unittest.TestCase):

    def test_string_parameter_when_none(self):
        parameter = create_parameter_model('param')

        error = parameter.validate_value(None)
        self.assertIsNone(error)

    @parameterized.expand([(None,), ('multiline_text',)])
    def test_text_parameter_when_value(self, param_type):
        parameter = create_parameter_model('param', type=param_type)

        error = parameter.validate_value('val')
        self.assertIsNone(error)

    def test_required_parameter_when_none(self):
        parameter = create_parameter_model('param', required=True)

        error = parameter.validate_value({})
        self.assert_error(error)

    @parameterized.expand([(None,), ('multiline_text',)])
    def test_required_parameter_when_empty(self, param_type):
        parameter = create_parameter_model('param', type=param_type, required=True)

        error = parameter.validate_value('')
        self.assert_error(error)

    def test_required_parameter_when_value(self):
        parameter = create_parameter_model('param', required=True)

        error = parameter.validate_value('val')
        self.assertIsNone(error)

    def test_required_parameter_when_constant(self):
        parameter = create_parameter_model('param', required=True, constant=True, default='123')

        error = parameter.validate_value(None)
        self.assertIsNone(error)

    def test_flag_parameter_when_true_bool(self):
        parameter = create_parameter_model('param', no_value=True)

        error = parameter.validate_value(True)
        self.assertIsNone(error)

    def test_flag_parameter_when_false_bool(self):
        parameter = create_parameter_model('param', no_value=True)

        error = parameter.validate_value(False)
        self.assertIsNone(error)

    def test_flag_parameter_when_true_string(self):
        parameter = create_parameter_model('param', no_value=True)

        error = parameter.validate_value('true')
        self.assertIsNone(error)

    def test_flag_parameter_when_false_string(self):
        parameter = create_parameter_model('param', no_value=True)

        error = parameter.validate_value('false')
        self.assertIsNone(error)

    def test_flag_parameter_when_some_string(self):
        parameter = create_parameter_model('param', no_value=True)

        error = parameter.validate_value('no')
        self.assert_error(error)

    def test_required_flag_parameter_when_true_boolean(self):
        parameter = create_parameter_model('param', no_value=True, required=True)

        error = parameter.validate_value(True)
        self.assertIsNone(error)

    def test_required_flag_parameter_when_false_boolean(self):
        parameter = create_parameter_model('param', no_value=True, required=True)

        error = parameter.validate_value(False)
        self.assertIsNone(error)

    def test_int_parameter_when_negative_int(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value(-100)
        self.assertIsNone(error)

    def test_int_parameter_when_large_positive_int(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value(1234567890987654321)
        self.assertIsNone(error)

    def test_int_parameter_when_zero_int_string(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value('0')
        self.assertIsNone(error)

    def test_int_parameter_when_large_negative_int_string(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value('-1234567890987654321')
        self.assertIsNone(error)

    def test_int_parameter_when_not_int_string(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value('v123')
        self.assert_error(error)

    def test_int_parameter_when_float(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value(1.2)
        self.assert_error(error)

    def test_int_parameter_when_float_string(self):
        parameter = create_parameter_model('param', type='int')

        error = parameter.validate_value('1.0')
        self.assert_error(error)

    def test_int_parameter_when_lower_than_max(self):
        parameter = create_parameter_model('param', type='int', max=100)

        error = parameter.validate_value(9)
        self.assertIsNone(error)

    def test_int_parameter_when_equal_to_max(self):
        parameter = create_parameter_model('param', type='int', max=5)

        error = parameter.validate_value(5)
        self.assertIsNone(error)

    def test_int_parameter_when_larger_than_max(self):
        parameter = create_parameter_model('param', type='int', max=0)

        error = parameter.validate_value(100)
        self.assert_error(error)

    def test_int_parameter_when_lower_than_min(self):
        parameter = create_parameter_model('param', type='int', min=100)

        error = parameter.validate_value(0)
        self.assert_error(error)

    def test_int_parameter_when_equal_to_min(self):
        parameter = create_parameter_model('param', type='int', min=-100)

        error = parameter.validate_value(-100)
        self.assertIsNone(error)

    def test_int_parameter_when_larger_than_min(self):
        parameter = create_parameter_model('param', type='int', min=100)

        error = parameter.validate_value(0)
        self.assert_error(error)

    def test_required_int_parameter_when_zero(self):
        parameter = create_parameter_model('param', type='int', required=True)

        error = parameter.validate_value(0)
        self.assertIsNone(error)

    def test_file_upload_parameter_when_valid(self):
        parameter = create_parameter_model('param', type='file_upload')

        uploaded_file = test_utils.create_file('test.xml')
        error = parameter.validate_value(uploaded_file)
        self.assertIsNone(error)

    def test_file_upload_parameter_when_not_exists(self):
        parameter = create_parameter_model('param', type='file_upload')

        uploaded_file = test_utils.create_file('test.xml')
        error = parameter.validate_value(uploaded_file + '_')
        self.assert_error(error)

    def test_list_parameter_when_matches(self):
        parameter = create_parameter_model(
            'param', type='list', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('val2')
        self.assertIsNone(error)

    def test_list_parameter_when_not_matches(self):
        parameter = create_parameter_model(
            'param', type='list', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('val4')
        self.assert_error(error)

    def test_editable_list_parameter_when_not_matches(self):
        parameter = create_parameter_model(
            'param', type='editable_list', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('val4')
        self.assertIsNone(error)

    def test_multiselect_when_empty_string(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('')
        self.assertIsNone(error)

    def test_multiselect_when_empty_list(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value([])
        self.assertIsNone(error)

    def test_multiselect_when_single_matching_element(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2'])
        self.assertIsNone(error)

    def test_multiselect_when_multiple_matching_elements(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2', 'val1'])
        self.assertIsNone(error)

    def test_multiselect_when_multiple_elements_one_not_matching(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2', 'val1', 'X'])
        self.assert_error(error)

    def test_multiselect_when_not_list_value(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('val1')
        self.assert_error(error)

    def test_multiselect_when_single_not_matching_element(self):
        parameter = create_parameter_model(
            'param', type=PARAM_TYPE_MULTISELECT, allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['X'])
        self.assert_error(error)

    def test_list_with_script_when_matches(self):
        parameter = create_parameter_model('param', type='list', values_script="echo '123\n' 'abc'")

        error = parameter.validate_value('123')
        self.assertIsNone(error)

    def test_list_with_script_when_matches_and_win_newline(self):
        parameter = create_parameter_model('param', type='list', values_script="echo '123\r\n' 'abc'")

        error = parameter.validate_value('123')
        self.assertIsNone(error)

    @parameterized.expand([
        ('a\d', 'ab', 'some desc', 'some desc'),
        ('a\d', '12', 'desc 2', 'desc 2'),
        ('a\d', 'a12', 'some long description', 'some long description'),
        ('\d+\wa+', 'aaaa', 'some desc', 'some desc'),
        ('\d+\wa+', 'aaaa', None, '\d+\wa+'),
    ])
    def test_regex_validation_when_fail_with_description(self, regex, value, description, expected_description):
        parameter = create_parameter_model('param', regex={'pattern': regex, 'description': description})

        error = parameter.validate_value(value)
        self.assert_error(error)
        self.assertEqual(error, "does not match regex pattern: " + expected_description)

    @parameterized.expand([
        ('a\d', 'a1',),
        ('\da', '2a',),
        ('a\d+', 'a12',),
        ('\d+\wa+', '1Xaaaa'),
        (None, '1Xaaaa'),
    ])
    def test_regex_validation_when_success(self, regex, value):
        parameter = create_parameter_model('param', regex={'pattern': regex})

        error = parameter.validate_value(value)
        self.assertIsNone(error)

    @parameterized.expand([(False,), (True,), (None,)])
    def test_list_with_dependency_when_matches(self, shell):
        parameters = []
        values = ObservableDict()
        dep_param = create_parameter_model('dep_param')
        parameter = create_parameter_model('param',
                                           type='list',
                                           values_script="echo '${dep_param}_\n' '_${dep_param}_'",
                                           all_parameters=parameters,
                                           other_param_values=values,
                                           values_script_shell=shell)
        parameters.extend([dep_param, parameter])

        values['dep_param'] = 'abc'
        error = parameter.validate_value(' _abc_')
        self.assertIsNone(error)

    def test_any_ip_when_ip4(self):
        parameter = create_parameter_model('param', type='ip')
        error = parameter.validate_value('127.0.0.1')
        self.assertIsNone(error)

    def test_any_ip_when_ip6(self):
        parameter = create_parameter_model('param', type='ip')
        error = parameter.validate_value('ABCD::6789')
        self.assertIsNone(error)

    def test_any_ip_when_wrong(self):
        parameter = create_parameter_model('param', type='ip')
        error = parameter.validate_value('127.abcd.1')
        self.assert_error(error)

    def test_ip4_when_valid(self):
        parameter = create_parameter_model('param', type='ip4')
        error = parameter.validate_value('192.168.0.13')
        self.assertIsNone(error)

    def test_ip4_when_ip6(self):
        parameter = create_parameter_model('param', type='ip4')
        error = parameter.validate_value('ABCD::1234')
        self.assert_error(error)

    def test_ip6_when_valid(self):
        parameter = create_parameter_model('param', type='ip6')
        error = parameter.validate_value('1:2:3:4:5:6:7:8')
        self.assertIsNone(error)

    def test_ip6_when_ip4(self):
        parameter = create_parameter_model('param', type='ip6')
        error = parameter.validate_value('172.13.0.15')
        self.assert_error(error)

    def test_ip6_when_complex_valid(self):
        parameter = create_parameter_model('param', type='ip6')
        error = parameter.validate_value('AbC:0::13:127.0.0.1')
        self.assertIsNone(error)

    def test_server_file_when_valid(self):
        filename = 'file1.txt'

        test_utils.create_file(filename)
        parameter = create_parameter_model('param', type=PARAM_TYPE_SERVER_FILE, file_dir=test_utils.temp_folder)

        error = parameter.validate_value(filename)
        self.assertIsNone(error)

    def test_server_file_when_wrong(self):
        test_utils.create_file('file1.txt')
        parameter = create_parameter_model('param', type=PARAM_TYPE_SERVER_FILE, file_dir=test_utils.temp_folder)

        error = parameter.validate_value('my.dat')
        self.assert_error(error)

    @parameterized.expand([(None,), ('multiline_text',)])
    def test_text_parameter_when_max_length_ok(self, param_type):
        parameter = create_parameter_model('param', type=param_type, max_length=10)

        error = parameter.validate_value('012345678\n')
        self.assertIsNone(error)

    @parameterized.expand([(None,), ('multiline_text',)])
    def test_text_parameter_when_max_length_violated(self, param_type):
        parameter = create_parameter_model('param', type=param_type, max_length=10)

        error = parameter.validate_value('0123456789\n')
        self.assert_error(error)

    def assert_error(self, error):
        self.assertFalse(is_blank(error), 'Expected validation error, but validation passed')

    def setUp(self):
        super().setUp()
        test_utils.setup()

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()


class ParameterValueNormalizationTest(unittest.TestCase):

    def test_normalize_simple_when_none(self):
        parameter = create_parameter_model('param')

        self.assertIsNone(parameter.normalize_user_value(None))

    def test_normalize_simple_when_string(self):
        parameter = create_parameter_model('param')

        self.assertEqual('abc', parameter.normalize_user_value('abc'))

    def test_normalize_simple_when_number(self):
        parameter = create_parameter_model('param')

        self.assertEqual(123, parameter.normalize_user_value(123))

    def test_normalize_simple_when_list(self):
        parameter = create_parameter_model('param')

        self.assertEqual(['Hello', 'world'], parameter.normalize_user_value(['Hello', 'world']))

    def test_normalize_multiselect_when_list(self):
        parameter = create_parameter_model('param', type=PARAM_TYPE_MULTISELECT, allowed_values=['Hello', 'world'])

        self.assertEqual(['Hello', 'world'], parameter.normalize_user_value(['Hello', 'world']))

    def test_normalize_multiselect_when_string(self):
        parameter = create_parameter_model('param', type=PARAM_TYPE_MULTISELECT, allowed_values=['Hello', 'world'])

        self.assertEqual(['world'], parameter.normalize_user_value('world'))

    def test_normalize_multiselect_when_none(self):
        parameter = create_parameter_model('param', type=PARAM_TYPE_MULTISELECT, allowed_values=['Hello', 'world'])

        self.assertEqual([], parameter.normalize_user_value(None))


class TestPassAsValue(unittest.TestCase):
    @parameterized.expand([
        ('argument', True, False, False),
        ('env_variable', False, True, False),
        ('EnV_VariablE', False, True, False),
        ('stdin', False, False, True),
        ('STDIN ', False, False, True),
        (None, True, True, False),
        ('unknown value', True, True, False),
    ])
    def test_pass_as(self, config, pass_as_arg, pass_as_env, pass_as_stdin):
        parameter = create_parameter_model('param', pass_as=config)

        pass_as = parameter.pass_as
        actual_value = (pass_as.pass_as_argument(), pass_as.pass_as_env_variable(), pass_as.pass_as_stdin())

        self.assertEqual((pass_as_arg, pass_as_env, pass_as_stdin), actual_value)


class TestStdinExpectedText(unittest.TestCase):

    @parameterized.expand([
        ('some text\nabc', 'some text\nabc'),
        (None, None),
    ])
    def test_stdin_expected_text(self, config, expected_value):
        parameter = create_parameter_model('param', stdin_expected_text=config)

        self.assertEqual(expected_value, parameter.stdin_expected_text)


class GetSortedParamConfig(unittest.TestCase):
    def test_get_sorted_when_3_fields(self):
        config = get_sorted_config({'type': 'int', 'name': 'Param X', 'required': True})

        expected = OrderedDict(
            [('name', 'Param X'),
             ('required', True),
             ('type', 'int')])
        self.assertEqual(expected, config)

    def test_get_sorted_when_many_fields(self):
        config = get_sorted_config({
            'separator': '/',
            'constant': False,
            'min': -10,
            'type': 'int',
            'default': 3,
            'name': 'Param X',
            'values': [],
            'required': True,
            'max': 5,
            'param': '-i',
            'description': 'guess number'
        })

        expected = OrderedDict(
            [('name', 'Param X'),
             ('required', True),
             ('param', '-i'),
             ('type', 'int'),
             ('default', 3),
             ('constant', False),
             ('description', 'guess number'),
             ('values', []),
             ('min', -10),
             ('max', 5),
             ('separator', '/')])
        self.assertEqual(expected, config)

    def test_get_sorted_when_unknown_fields(self):
        config = get_sorted_config({
            'key1': 'abc',
            'file_recursive': True,
            'key2': 123,
            'name': 'Param X',
            'key3': []})

        expected = OrderedDict(
            [('name', 'Param X'),
             ('file_recursive', True),
             ('key1', 'abc'),
             ('key2', 123),
             ('key3', [])])

        self.assertEqual(expected.popitem(last=False), config.popitem(last=False))
        self.assertEqual(expected.popitem(last=False), config.popitem(last=False))
        self.assertCountEqual(expected.items(), config.items())


def _create_parameter_model(config, *, username=DEF_USERNAME, audit_name=DEF_AUDIT_NAME, all_parameters=None):
    return create_parameter_model_from_config(config,
                                              username=username,
                                              audit_name=audit_name,
                                              all_parameters=all_parameters)
