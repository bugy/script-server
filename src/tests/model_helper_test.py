import os
import unittest

from model import script_configs
from model.model_helper import read_list, read_dict, prepare_multiselect_values, fill_parameter_values
from tests.test_utils import create_parameter_model


class TestDefaultValue(unittest.TestCase):
    env_key = 'test_val'

    def test_no_value(self):
        default = script_configs._resolve_default(None, None, None)

        self.assertEqual(default, None)

    def test_empty_value(self):
        default = script_configs._resolve_default('', None, None)

        self.assertEqual(default, '')

    def test_text_value(self):
        default = script_configs._resolve_default('text', None, None)

        self.assertEqual(default, 'text')

    def test_unicode_value(self):
        default = script_configs._resolve_default(u'text', None, None)

        self.assertEqual(default, u'text')

    def test_int_value(self):
        default = script_configs._resolve_default(5, None, None)

        self.assertEqual(default, 5)

    def test_bool_value(self):
        default = script_configs._resolve_default(True, None, None)

        self.assertEqual(default, True)

    def test_env_variable(self):
        os.environ[self.env_key] = 'text'

        default = script_configs._resolve_default('$$test_val', None, None)

        self.assertEqual(default, 'text')

    def test_missing_env_variable(self):
        self.assertRaises(Exception, script_configs._resolve_default, '$$test_val', None, None)

    def test_auth_username(self):
        default = script_configs._resolve_default('${auth.username}', 'buggy', None)
        self.assertEqual('buggy', default)

    def test_auth_username_when_none(self):
        default = script_configs._resolve_default('${auth.username}', None, None)
        self.assertEqual('', default)

    def test_auth_username_when_inside_text(self):
        default = script_configs._resolve_default('__${auth.username}__', 'usx', None)
        self.assertEqual('__usx__', default)

    def test_auth_audit_name(self):
        default = script_configs._resolve_default('${auth.audit_name}', None, '127.0.0.1')
        self.assertEqual('127.0.0.1', default)

    def test_auth_audit_name_when_none(self):
        default = script_configs._resolve_default('${auth.audit_name}', None, None)
        self.assertEqual('', default)

    def test_auth_audit_name_when_inside_text(self):
        default = script_configs._resolve_default('__${auth.audit_name}__', None, 'usx')
        self.assertEqual('__usx__', default)

    def test_auth_username_and_audit_name(self):
        default = script_configs._resolve_default('${auth.username}:${auth.audit_name}', 'buggy', 'localhost')
        self.assertEqual('buggy:localhost', default)

    def tearDown(self):
        if self.env_key in os.environ:
            del os.environ[self.env_key]


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
        parameter = create_parameter_model('param', type='multiselect')

        values = self.prepare({parameter: 'val1'})
        self.assertEqual(['val1'], values['param'])

    def test_prepare_empty_string(self):
        parameter = create_parameter_model('param', type='multiselect')

        values = self.prepare({parameter: ''})
        self.assertEqual([], values['param'])

    def test_prepare_empty_list(self):
        parameter = create_parameter_model('param', type='multiselect')

        values = self.prepare({parameter: []})
        self.assertEqual([], values['param'])

    def test_prepare_some_list(self):
        parameter = create_parameter_model('param', type='multiselect')

        values = self.prepare({parameter: ['v1', 'v2']})
        self.assertEqual(['v1', 'v2'], values['param'])

    def test_prepare_only_multiselect(self):
        parameters = []
        param1 = create_parameter_model('param1', type='text', all_parameters=parameters)
        multi_param = create_parameter_model('multi_param', type='multiselect', all_parameters=parameters)
        param2 = create_parameter_model('param2', type='list', all_parameters=parameters)

        parameters.extend([param1, multi_param, param2])

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
            parameter = create_parameter_model(name, all_parameters=result)
            result.append(parameter)

        return result
