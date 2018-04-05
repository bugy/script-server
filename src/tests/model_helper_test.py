import os
import unittest

from model import model_helper
from model import script_configs
from model.model_helper import read_list, read_dict
from tests import test_utils


class TestDefaultValue(unittest.TestCase):
    env_key = 'test_val'

    def test_no_value(self):
        parameter = script_configs.Parameter()

        default = model_helper.get_default(parameter)
        self.assertEqual(default, None)

    def test_empty_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, '')

    def test_text_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('text')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_unicode_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(u'text')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, u'text')

    def test_int_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(5)

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 5)

    def test_bool_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(True)

        default = model_helper.get_default(parameter)
        self.assertEqual(default, True)

    def test_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        os.environ[self.env_key] = 'text'

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_missing_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        self.assertRaises(Exception, model_helper.get_default, parameter)

    def tearDown(self):
        if self.env_key in os.environ:
            del os.environ[self.env_key]


class TestParametersValidation(unittest.TestCase):
    def test_no_parameters(self):
        script_config = script_configs.Config()

        valid = model_helper.validate_parameters({}, script_config)
        self.assertTrue(valid)

    def test_string_parameter_when_none(self):
        script_config = script_configs.Config()
        self.add_parameter('param', script_config)

        valid = model_helper.validate_parameters({}, script_config)
        self.assertTrue(valid)

    def test_string_parameter_when_value(self):
        script_config = script_configs.Config()
        self.add_parameter('param', script_config)

        valid = model_helper.validate_parameters({'param': 'val'}, script_config)
        self.assertTrue(valid)

    def test_required_parameter_when_none(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.required = True

        valid = model_helper.validate_parameters({}, script_config)
        self.assertFalse(valid)

    def test_required_parameter_when_empty(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.required = True

        valid = model_helper.validate_parameters({'param': ''}, script_config)
        self.assertFalse(valid)

    def test_required_parameter_when_value(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.required = True

        valid = model_helper.validate_parameters({'param': 'val'}, script_config)
        self.assertTrue(valid)

    def test_required_parameter_when_constant(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.required = True
        parameter.constant = True

        valid = model_helper.validate_parameters({}, script_config)
        self.assertTrue(valid)

    def test_flag_parameter_when_true_bool(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True

        valid = model_helper.validate_parameters({'param': True}, script_config)
        self.assertTrue(valid)

    def test_flag_parameter_when_false_bool(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True

        valid = model_helper.validate_parameters({'param': False}, script_config)
        self.assertTrue(valid)

    def test_flag_parameter_when_true_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True

        valid = model_helper.validate_parameters({'param': 'true'}, script_config)
        self.assertTrue(valid)

    def test_flag_parameter_when_false_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True

        valid = model_helper.validate_parameters({'param': 'false'}, script_config)
        self.assertTrue(valid)

    def test_flag_parameter_when_some_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True

        valid = model_helper.validate_parameters({'param': 'no'}, script_config)
        self.assertFalse(valid)

    def test_required_flag_parameter_when_true_boolean(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True
        parameter.required = True

        valid = model_helper.validate_parameters({'param': True}, script_config)
        self.assertTrue(valid)

    def test_required_flag_parameter_when_false_boolean(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.no_value = True
        parameter.required = True

        valid = model_helper.validate_parameters({'param': False}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_negative_int(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': -100}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_large_positive_int(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': 1234567890987654321}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_zero_int_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': '0'}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_large_negative_int_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': '-1234567890987654321'}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_not_int_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': 'v123'}, script_config)
        self.assertFalse(valid)

    def test_int_parameter_when_float(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': 1.2}, script_config)
        self.assertFalse(valid)

    def test_int_parameter_when_float_string(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'

        valid = model_helper.validate_parameters({'param': '1.0'}, script_config)
        self.assertFalse(valid)

    def test_int_parameter_when_lower_than_max(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.max = 100

        valid = model_helper.validate_parameters({'param': 9}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_equal_to_max(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.max = 5

        valid = model_helper.validate_parameters({'param': 5}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_larger_than_max(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.max = 0

        valid = model_helper.validate_parameters({'param': 100}, script_config)
        self.assertFalse(valid)

    def test_int_parameter_when_lower_than_min(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.min = 100

        valid = model_helper.validate_parameters({'param': 0}, script_config)
        self.assertFalse(valid)

    def test_int_parameter_when_equal_to_min(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.min = -100

        valid = model_helper.validate_parameters({'param': -100}, script_config)
        self.assertTrue(valid)

    def test_int_parameter_when_larger_than_min(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.min = 100

        valid = model_helper.validate_parameters({'param': 0}, script_config)
        self.assertFalse(valid)

    def test_required_int_parameter_when_zero(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'int'
        parameter.required = True

        valid = model_helper.validate_parameters({'param': 0}, script_config)
        self.assertTrue(valid)

    def test_file_upload_parameter_when_valid(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'file_upload'

        uploaded_file = test_utils.create_file('test.xml')
        valid = model_helper.validate_parameters({'param': uploaded_file}, script_config)
        self.assertTrue(valid)

    def test_file_upload_parameter_when_not_exists(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'file_upload'

        uploaded_file = test_utils.create_file('test.xml')
        valid = model_helper.validate_parameters({'param': uploaded_file + '_'}, script_config)
        self.assertFalse(valid)

    def test_list_parameter_when_matches(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'list'
        parameter.values = ['val1', 'val2', 'val3']

        valid = model_helper.validate_parameters({'param': 'val2'}, script_config)
        self.assertTrue(valid)

    def test_list_parameter_when_not_matches(self):
        script_config = script_configs.Config()

        parameter = self.add_parameter('param', script_config)
        parameter.type = 'list'
        parameter.values = ['val1', 'val2', 'val3']

        valid = model_helper.validate_parameters({'param': 'val4'}, script_config)
        self.assertFalse(valid)

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
