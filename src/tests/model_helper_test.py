import os
import unittest

import model.script_configs
from config.script.list_values import ConstValuesProvider, ValuesProvider
from model import model_helper
from model import script_configs
from model.model_helper import read_list, read_dict, prepare_multiselect_values, fill_parameter_values
from tests import test_utils
from utils.string_utils import is_blank


class TestDefaultValue(unittest.TestCase):
    env_key = 'test_val'

    def test_no_value(self):
        parameter = script_configs.Parameter()

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, None)

    def test_empty_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('')

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, '')

    def test_text_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('text')

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_unicode_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(u'text')

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, u'text')

    def test_int_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(5)

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, 5)

    def test_bool_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(True)

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, True)

    def test_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        os.environ[self.env_key] = 'text'

        default = model.script_configs.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_missing_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        self.assertRaises(Exception, model.script_configs.get_default, parameter)

    def tearDown(self):
        if self.env_key in os.environ:
            del os.environ[self.env_key]


class TestParametersValidation(unittest.TestCase):
    def test_no_parameters(self):
        script_config = script_configs.Config()

        valid = model_helper.validate_parameters({}, script_config)
        self.assertTrue(valid)

    def test_multiple_required_parameters_when_all_defined(self):
        script_config = script_configs.Config()

        values = {}
        for i in range(0, 5):
            parameter = self.add_parameter('param' + str(i), script_config)
            parameter.required = True

            values[parameter.name] = str(i)

        valid = model_helper.validate_parameters(values, script_config)
        self.assertTrue(valid)

    def test_multiple_required_parameters_when_one_missing(self):
        script_config = script_configs.Config()

        values = {}
        for i in range(0, 5):
            parameter = self.add_parameter('param' + str(i), script_config)
            parameter.required = True

            if i != 4:
                values[parameter.name] = str(i)

        valid = model_helper.validate_parameters(values, script_config)
        self.assertFalse(valid)

    def test_multiple_parameters_when_all_defined(self):
        script_config = script_configs.Config()

        values = {}
        for i in range(0, 5):
            parameter = self.add_parameter('param' + str(i), script_config)
            values[parameter.name] = str(i)

        valid = model_helper.validate_parameters(values, script_config)
        self.assertTrue(valid)

    def test_multiple_parameters_when_all_missing(self):
        script_config = script_configs.Config()

        for i in range(0, 5):
            self.add_parameter('param' + str(i), script_config)

        valid = model_helper.validate_parameters({}, script_config)
        self.assertTrue(valid)

    def test_multiple_int_parameters_when_all_valid(self):
        script_config = script_configs.Config()

        values = {}
        for i in range(0, 5):
            parameter = self.add_parameter('param' + str(i), script_config)
            parameter.type = 'int'

            values[parameter.name] = i

        valid = model_helper.validate_parameters(values, script_config)
        self.assertTrue(valid)

    def test_multiple_int_parameters_when_one_invalid(self):
        script_config = script_configs.Config()

        values = {}
        for i in range(0, 5):
            parameter = self.add_parameter('param' + str(i), script_config)
            parameter.type = 'int'

            if i != 4:
                values[parameter.name] = i
            else:
                values[parameter.name] = 'val'

        valid = model_helper.validate_parameters(values, script_config)
        self.assertFalse(valid)

    def add_parameter(self, name, script_config):
        parameter = script_configs.Parameter()
        parameter.name = name
        script_config.add_parameter(parameter)

        return parameter

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestSingleParameterValidation(unittest.TestCase):

    def test_string_parameter_when_none(self):
        parameter = self.create_parameter('param')

        error = model_helper.validate_parameter(parameter, {})
        self.assertIsNone(error)

    def test_string_parameter_when_value(self):
        parameter = self.create_parameter('param')

        error = model_helper.validate_parameter(parameter, {'param': 'val'})
        self.assertIsNone(error)

    def test_required_parameter_when_none(self):
        parameter = self.create_parameter('param')
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {})
        self.assert_error(error)

    def test_required_parameter_when_empty(self):
        parameter = self.create_parameter('param')
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {'param': ''})
        self.assert_error(error)

    def test_required_parameter_when_value(self):
        parameter = self.create_parameter('param')
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {'param': 'val'})
        self.assertIsNone(error)

    def test_required_parameter_when_constant(self):
        parameter = self.create_parameter('param')
        parameter.required = True
        parameter.constant = True

        error = model_helper.validate_parameter(parameter, {})
        self.assertIsNone(error)

    def test_flag_parameter_when_true_bool(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True

        error = model_helper.validate_parameter(parameter, {'param': True})
        self.assertIsNone(error)

    def test_flag_parameter_when_false_bool(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True

        error = model_helper.validate_parameter(parameter, {'param': False})
        self.assertIsNone(error)

    def test_flag_parameter_when_true_string(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True

        error = model_helper.validate_parameter(parameter, {'param': 'true'})
        self.assertIsNone(error)

    def test_flag_parameter_when_false_string(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True

        error = model_helper.validate_parameter(parameter, {'param': 'false'})
        self.assertIsNone(error)

    def test_flag_parameter_when_some_string(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True

        error = model_helper.validate_parameter(parameter, {'param': 'no'})
        self.assert_error(error)

    def test_required_flag_parameter_when_true_boolean(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {'param': True})
        self.assertIsNone(error)

    def test_required_flag_parameter_when_false_boolean(self):
        parameter = self.create_parameter('param')
        parameter.no_value = True
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {'param': False})
        self.assertIsNone(error)

    def test_int_parameter_when_negative_int(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': -100})
        self.assertIsNone(error)

    def test_int_parameter_when_large_positive_int(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': 1234567890987654321})
        self.assertIsNone(error)

    def test_int_parameter_when_zero_int_string(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': '0'})
        self.assertIsNone(error)

    def test_int_parameter_when_large_negative_int_string(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': '-1234567890987654321'})
        self.assertIsNone(error)

    def test_int_parameter_when_not_int_string(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': 'v123'})
        self.assert_error(error)

    def test_int_parameter_when_float(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': 1.2})
        self.assert_error(error)

    def test_int_parameter_when_float_string(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'

        error = model_helper.validate_parameter(parameter, {'param': '1.0'})
        self.assert_error(error)

    def test_int_parameter_when_lower_than_max(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.max = 100

        error = model_helper.validate_parameter(parameter, {'param': 9})
        self.assertIsNone(error)

    def test_int_parameter_when_equal_to_max(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.max = 5

        error = model_helper.validate_parameter(parameter, {'param': 5})
        self.assertIsNone(error)

    def test_int_parameter_when_larger_than_max(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.max = 0

        error = model_helper.validate_parameter(parameter, {'param': 100})
        self.assert_error(error)

    def test_int_parameter_when_lower_than_min(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.min = 100

        error = model_helper.validate_parameter(parameter, {'param': 0})
        self.assert_error(error)

    def test_int_parameter_when_equal_to_min(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.min = -100

        error = model_helper.validate_parameter(parameter, {'param': -100})
        self.assertIsNone(error)

    def test_int_parameter_when_larger_than_min(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.min = 100

        error = model_helper.validate_parameter(parameter, {'param': 0})
        self.assert_error(error)

    def test_required_int_parameter_when_zero(self):
        parameter = self.create_parameter('param')
        parameter.type = 'int'
        parameter.required = True

        error = model_helper.validate_parameter(parameter, {'param': 0})
        self.assertIsNone(error)

    def test_file_upload_parameter_when_valid(self):
        parameter = self.create_parameter('param')
        parameter.type = 'file_upload'

        uploaded_file = test_utils.create_file('test.xml')
        error = model_helper.validate_parameter(parameter, {'param': uploaded_file})
        self.assertIsNone(error)

    def test_file_upload_parameter_when_not_exists(self):
        parameter = self.create_parameter('param')
        parameter.type = 'file_upload'

        uploaded_file = test_utils.create_file('test.xml')
        error = model_helper.validate_parameter(parameter, {'param': uploaded_file + '_'})
        self.assert_error(error)

    def test_list_parameter_when_matches(self):
        parameter = self.create_parameter('param')
        parameter.type = 'list'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': 'val2'})
        self.assertIsNone(error)

    def test_list_parameter_when_not_matches(self):
        parameter = self.create_parameter('param')
        parameter.type = 'list'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': 'val4'})
        self.assert_error(error)

    def test_multiselect_when_empty_string(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': ''})
        self.assertIsNone(error)

    def test_multiselect_when_empty_list(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': []})
        self.assertIsNone(error)

    def test_multiselect_when_single_matching_element(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': ['val2']})
        self.assertIsNone(error)

    def test_multiselect_when_multiple_matching_elements(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': ['val2', 'val1']})
        self.assertIsNone(error)

    def test_multiselect_when_multiple_elements_one_not_matching(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': ['val2', 'val1', 'X']})
        self.assert_error(error)

    def test_multiselect_when_not_list_value(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': 'val1'})
        self.assert_error(error)

    def test_multiselect_when_single_not_matching_element(self):
        parameter = self.create_parameter('param')
        parameter.type = 'multiselect'
        parameter.values_provider = ConstValuesProvider(['val1', 'val2', 'val3'])

        error = model_helper.validate_parameter(parameter, {'param': ['X']})
        self.assert_error(error)

    def test_list_with_dependency_when_matches(self):
        parameter = self.create_parameter('param')
        parameter.type = 'list'
        parameter.values_provider = _DependantScriptValuesProvider(['dep_param'])

        error = model_helper.validate_parameter(parameter, {'param': 'abc_1', 'dep_param': 'abc'})
        self.assertIsNone(error)

    def test_list_with_dependency_when_not_matches(self):
        parameter = self.create_parameter('param')
        parameter.type = 'list'
        parameter.values_provider = _DependantScriptValuesProvider(['dep_param'])

        error = model_helper.validate_parameter(parameter, {'param': 'ZZZ', 'dep_param': 'value_A'})
        self.assert_error(error)

    def test_list_with_dependency_when_matches_multiple(self):
        parameter = self.create_parameter('param')
        parameter.type = 'list'
        parameter.values_provider = _DependantScriptValuesProvider(['dp1', 'dp2', 'dp3'])

        error = model_helper.validate_parameter(parameter, {'param': 'x_y_z_3',
                                                            'dp1': 'x', 'dp2': 'y', 'dp3': 'z'})
        self.assertIsNone(error)

    def assert_error(self, error):
        self.assertFalse(is_blank(error), 'Expected validation error, but validation passed')

    def create_parameter(self, param_name):
        parameter = script_configs.Parameter()
        parameter.name = param_name
        return parameter


class TestReadList(unittest.TestCase):
    def test_simple_list(self):
        values_dict = {'list_key': [1, 2, 3]}
        list_value = read_list(values_dict, 'list_key')
        self.assertEqual(list_value, [1, 2, 3])

    def test_single_value(self):
        values_dict = {'list_key': 'hello'}
        list_value = read_list(values_dict, 'list_key')
        self.assertEqual(list_value, ['hello'])

    def test_empty_single_value(self):
        values_dict = {'list_key': ''}
        list_value = read_list(values_dict, 'list_key')
        self.assertEqual(list_value, [''])

    def test_default_value_when_missing(self):
        values_dict = {'another_key': 'hello'}
        list_value = read_list(values_dict, 'list_key')
        self.assertEqual(list_value, [])

    def test_default_value_when_specified(self):
        values_dict = {'another_key': 'hello'}
        list_value = read_list(values_dict, 'list_key', [True, False])
        self.assertEqual(list_value, [True, False])

    def test_dict_not_allowed_value(self):
        values_dict = {'list_key': {'key1': 'value1'}}
        self.assertRaises(Exception, read_list, values_dict, 'list_key')


class TestReadDict(unittest.TestCase):
    def test_simple_dict(self):
        values_dict = {'dict_key': {'key1': 'value1', 'key2': 'value2'}}
        dict_value = read_dict(values_dict, 'dict_key')
        self.assertEqual(dict_value, {'key1': 'value1', 'key2': 'value2'})

    def test_list_value_not_allowed(self):
        values_dict = {'dict_key': [1, 2]}
        self.assertRaises(Exception, read_dict, values_dict, 'dict_key')

    def test_single_value_not_allowed(self):
        values_dict = {'dict_key': 'hello'}
        self.assertRaises(Exception, read_dict, values_dict, 'dict_key')

    def test_empty_value_not_allowed(self):
        values_dict = {'dict_key': ''}
        self.assertRaises(Exception, read_dict, values_dict, 'dict_key')

    def test_empty_dict(self):
        values_dict = {'dict_key': {}}
        dict_value = read_dict(values_dict, 'dict_key', {'key1': 'value1'})
        self.assertEqual(dict_value, {})

    def test_default_when_missing(self):
        values_dict = {'another_key': {'key1': 'value1'}}
        dict_value = read_dict(values_dict, 'dict_key')
        self.assertEqual(dict_value, {})

    def test_default_when_specified(self):
        values_dict = {'another_key': {'key1': 'value1'}}
        dict_value = read_dict(values_dict, 'dict_key', {'key2': 'value2'})
        self.assertEqual(dict_value, {'key2': 'value2'})


class TestPrepareMultiselectValues(unittest.TestCase):

    def test_prepare_single_value(self):
        parameter = self.create_parameter('param', 'multiselect')

        values = self.prepare({parameter: 'val1'})
        self.assertEqual(['val1'], values['param'])

    def test_prepare_empty_string(self):
        parameter = self.create_parameter('param', 'multiselect')

        values = self.prepare({parameter: ''})
        self.assertEqual([], values['param'])

    def test_prepare_empty_list(self):
        parameter = self.create_parameter('param', 'multiselect')

        values = self.prepare({parameter: []})
        self.assertEqual([], values['param'])

    def test_prepare_some_list(self):
        parameter = self.create_parameter('param', 'multiselect')

        values = self.prepare({parameter: ['v1', 'v2']})
        self.assertEqual(['v1', 'v2'], values['param'])

    def test_prepare_only_multiselect(self):
        param1 = self.create_parameter('param1', 'text')
        multi_param = self.create_parameter('multi_param', 'multiselect')
        param2 = self.create_parameter('param2', 'list')

        values = self.prepare({
            param1: 'xyz',
            multi_param: 'xyz',
            param2: 'xyz'})
        self.assertEqual('xyz', values['param1'])
        self.assertEqual(['xyz'], values['multi_param'])
        self.assertEqual('xyz', values['param2'])

    def prepare(self, parameter_values):
        values = {param.name: value for param, value in parameter_values.items()}
        parameters = list(parameter_values.keys())
        prepare_multiselect_values(values, parameters)
        return values

    def create_parameter(self, name, type):
        parameter = script_configs.Parameter()
        parameter.name = name
        parameter.type = type
        return parameter


class TestFillParameterValues(unittest.TestCase):
    def test_fill_single_parameter(self):
        result = fill_parameter_values(self.create_parameters('p1'), 'Hello, ${p1}!', {'p1': 'world'})
        self.assertEqual('Hello, world!', result)

    def test_fill_single_parameter_multiple_times(self):
        result = fill_parameter_values(self.create_parameters('p1'), 'Ho${p1}-${p1}${p1}!', {'p1': 'ho'})
        self.assertEqual('Hoho-hoho!', result)

    def test_fill_multiple_parameters(self):
        result = fill_parameter_values(self.create_parameters('p1', 'p2', 'p3'),
                                       'Some ${p2} text, which is ${p3} by ${p1}.',
                                       {'p1': 'script-server', 'p2': 'small', 'p3': 'generated'})
        self.assertEqual('Some small text, which is generated by script-server.', result)

    def test_fill_multiple_parameters_when_one_without_value(self):
        result = fill_parameter_values(self.create_parameters('p1', 'p2'),
                                       '${p1} vs ${p2}',
                                       {'p1': 'ABC'})
        self.assertEqual('ABC vs ', result)

    def test_fill_multiple_parameters_when_one_secure(self):
        parameters = self.create_parameters('p1', 'p2')
        parameters[1].secure = True
        result = fill_parameter_values(parameters,
                                       '${p1} vs ${p2}',
                                       {'p1': 'ABC', 'p2': 'XYZ'})
        self.assertEqual('ABC vs ${p2}', result)

    def test_fill_non_string_value(self):
        result = fill_parameter_values(self.create_parameters('p1'), 'Value = ${p1}', {'p1': 5})
        self.assertEqual('Value = 5', result)

    def test_fill_when_no_parameter_for_pattern(self):
        result = fill_parameter_values(self.create_parameters('p1'), 'Value = ${xyz}', {'p1': '12345'})
        self.assertEqual('Value = ${xyz}', result)

    def create_parameters(self, *names):
        result = []
        for name in names:
            parameter = script_configs.Parameter()
            parameter.name = name
            result.append(parameter)

        return result


class _DependantScriptValuesProvider(ValuesProvider):

    def __init__(self, required_parameters) -> None:
        self.required_parameters = required_parameters

    def get_required_parameters(self):
        return self.required_parameters

    def get_values(self, parameter_values):
        value_base = ''
        for required_parameter in self.required_parameters:
            value_base += parameter_values[required_parameter] + '_'

        return [value_base + '1', value_base + '2', value_base + '3']
