import os
import unittest

from model.script_configs import ConfigModel, InvalidValueException, _TemplateProperty
from react.properties import ObservableDict, ObservableList
from tests import test_utils
from tests.test_utils import create_script_param_config, create_parameter_model, create_parameter_model_from_config
from utils import file_utils
from utils.string_utils import is_blank

DEF_AUDIT_NAME = '127.0.0.1'
DEF_USERNAME = 'user1'


class ConfigModelInitTest(unittest.TestCase):
    def test_create_empty_config(self):
        model = _create_config_model('conf_x')
        self.assertEqual('conf_x', model.name)

    def test_create_full_config(self):
        name = 'conf_y'
        script_path = '/path/to/script'
        description = 'A script for test_create_full_config'
        working_directory = '/root'
        requires_terminal = False
        bash_formatting = True
        output_files = ['file1', 'file2']

        config_model = _create_config_model(name, config={
            'script_path': script_path,
            'description': description,
            'working_directory': working_directory,
            'requires_terminal': requires_terminal,
            'bash_formatting': bash_formatting,
            'output_files': output_files})

        self.assertEqual(name, config_model.name)
        self.assertEqual(script_path, config_model.script_command)
        self.assertEqual(description, config_model.description)
        self.assertEqual(working_directory, config_model.working_directory)
        self.assertEqual(requires_terminal, config_model.requires_terminal)
        self.assertEqual(bash_formatting, config_model.ansi_enabled)
        self.assertEqual(output_files, config_model.output_files)

    def test_create_with_parameter(self):
        config_model = _create_config_model('conf_p_1', parameters=[create_script_param_config('param1')])
        self.assertEqual(1, len(config_model.parameters))
        self.assertEqual('param1', config_model.parameters[0].name)

    def test_create_with_parameters_and_default_values(self):
        parameters = [create_script_param_config('param1', default='123'),
                      create_script_param_config('param2'),
                      create_script_param_config('param3', default='A')]
        config_model = _create_config_model('conf_with_defaults', parameters=parameters)
        self.assertEqual(3, len(config_model.parameters))

        values = config_model.parameter_values
        self.assertEqual('123', values.get('param1'))
        self.assertIsNone(values.get('param2'))
        self.assertEqual('A', values.get('param3'))

    def test_create_with_parameters_and_custom_values(self):
        parameters = [create_script_param_config('param1', default='def1'),
                      create_script_param_config('param2', default='def2'),
                      create_script_param_config('param3', default='def3')]
        parameter_values = {'param1': '123', 'param3': True}
        config_model = _create_config_model('conf_with_defaults', parameters=parameters,
                                            parameter_values=parameter_values)
        self.assertEqual(3, len(config_model.parameters))

        values = config_model.parameter_values
        self.assertEqual('123', values.get('param1'))
        self.assertIsNone(values.get('param2'))
        self.assertEqual(True, values.get('param3'))

    def test_create_with_missing_dependant_parameter(self):
        parameters = [create_script_param_config('param1', type='list', values_script='echo ${p2}')]
        self.assertRaisesRegex(Exception, 'Missing parameter "p2"', _create_config_model, 'conf', parameters=parameters)

    def test_create_with_secure_dependant_parameter(self):
        parameters = [create_script_param_config('param1', type='list', values_script='echo ${p2}'),
                      create_script_param_config('p2', secure=True)]
        self.assertRaisesRegex(Exception, 'Unsupported parameter "p2"',
                               _create_config_model, 'conf', parameters=parameters)

    def test_create_with_no_value_dependant_parameter(self):
        parameters = [create_script_param_config('param1', type='list', values_script='echo ${p2}'),
                      create_script_param_config('p2', no_value=True)]
        self.assertRaisesRegex(Exception, 'Unsupported parameter "p2"',
                               _create_config_model, 'conf', parameters=parameters)


class ConfigModelValuesTest(unittest.TestCase):

    def test_set_value(self):
        param1 = create_script_param_config('param1')
        config_model = _create_config_model('conf_x', parameters=[param1])
        config_model.set_param_value('param1', 'abc')

        self.assertEqual({'param1': 'abc'}, config_model.parameter_values)

    def test_set_value_for_unknown_parameter(self):
        param1 = create_script_param_config('param1')
        config_model = _create_config_model('conf_x', parameters=[param1])

        config_model.set_param_value('PAR_2', 'abc')

        self.assertNotIn('PAR_2', config_model.parameter_values)

    def test_set_all_values_when_dependant_before_required(self):
        parameters = [
            create_script_param_config('dep_p2', type='list', values_script='echo "X${p1}X"'),
            create_script_param_config('p1')]

        config_model = _create_config_model('main_conf', parameters=parameters)

        values = {'dep_p2': 'XabcX', 'p1': 'abc'}
        config_model.set_all_param_values(values)

        self.assertEqual(values, config_model.parameter_values)

    def test_set_all_values_when_dependants_cylce(self):
        parameters = [
            create_script_param_config('p1', type='list', values_script='echo "X${p2}X"'),
            create_script_param_config('p2', type='list', values_script='echo "X${p1}X"')]

        config_model = _create_config_model('main_conf', parameters=parameters)

        values = {'p1': 'XabcX', 'p2': 'abc'}
        self.assertRaisesRegex(Exception, 'Could not resolve order', config_model.set_all_param_values, values)


class ConfigModelObserverTest(unittest.TestCase):
    def test_property_notification_on_field_change(self):
        config = _create_config_model('conf_x')
        changes = []
        config.description_prop.subscribe(lambda old, new: changes.append(new))
        config.description = 'new desc'

        self.assertEqual(['new desc'], changes)

    def test_global_notification_on_field_change(self):
        config = _create_config_model('conf_x')
        changes = []
        config.subscribe(lambda prop, old, new: changes.append((prop, new)))
        config.description = 'new desc'

        self.assertEqual([('description', 'new desc')], changes)

    def test_notification_on_parameter_add(self):
        config = _create_config_model('conf_x')
        observer = self._create_collection_observer()
        config.parameters.subscribe(observer)

        parameter = create_parameter_model('param1')
        config.parameters.append(parameter)

        self.assertEqual([('add', parameter)], observer.changes)

    def test_notification_on_parameter_remove(self):
        config = _create_config_model('conf_x', parameters=[create_script_param_config('param1')])
        param1 = config.find_parameter('param1')

        observer = self._create_collection_observer()
        config.parameters.subscribe(observer)

        config.parameters.remove(param1)

        self.assertEqual([('remove', param1)], observer.changes)

    def _create_collection_observer(self):
        class _CollectionObserver:
            def __init__(self) -> None:
                self.changes = []

            def on_add(self, value, index):
                self.changes.append(('add', value))

            def on_remove(self, value):
                self.changes.append(('remove', value))

        return _CollectionObserver()


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
            'no_value': 'true',
            'description': description,
            'required': required,
            'min': min,
            'max': max,
            'separator': separator,
            'multiple_arguments': 'True',
            'default': default,
            'type': type,
            'constant': 'false',
            'values': values
        })

        self.assertEqual(name, parameter_model.name)
        self.assertEqual(name, parameter_model.name)
        self.assertEqual(param, parameter_model.param)
        self.assertEqual(True, parameter_model.no_value)
        self.assertEqual(description, parameter_model.description)
        self.assertEqual(required, parameter_model.required)
        self.assertEqual(min, parameter_model.min)
        self.assertEqual(max, parameter_model.max)
        self.assertEqual(separator, parameter_model.separator)
        self.assertEqual(True, parameter_model.multiple_arguments)
        self.assertEqual(default, parameter_model.default)
        self.assertEqual(type, parameter_model.type)
        self.assertEqual(False, parameter_model.constant)
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

    def test_resolve_default(self):
        parameter_model = _create_parameter_model({'name': 'def_param', 'default': 'X${auth.username}X'})
        self.assertEqual('X' + DEF_USERNAME + 'X', parameter_model.default)

    def test_prohibit_constant_without_default(self):
        self.assertRaisesRegex(Exception, 'Constant should have default value specified',
                               _create_parameter_model, {'name': 'def_param', 'constant': 'true'})

    def test_values_from_script(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'list',
            'values': {'script': 'echo "123\n" "456"'}})
        self.assertEqual(['123', ' 456'], parameter_model.values)

    def test_allowed_values_for_non_list(self):
        parameter_model = _create_parameter_model({
            'name': 'def_param',
            'type': 'int',
            'values': {'script': 'echo "123\n" "456"'}})
        self.assertEqual(None, parameter_model.values)


class ParameterModelDependantValuesTest(unittest.TestCase):
    def test_get_parameter_values_simple(self):
        parameters = [
            create_script_param_config('p1'),
            create_script_param_config('dependant',
                                       type='list',
                                       values_script="echo '${p1}\n' '_${p1}_\n' '${p1}${p1}\n'")
        ]
        config_model = _create_config_model('conf_x', parameters=parameters)
        config_model.set_param_value('p1', 'ABC')

        dependant_parameter = config_model.find_parameter('dependant')

        self.assertEqual(['ABC', ' _ABC_', ' ABCABC'], dependant_parameter.values)

    def test_get_parameter_values_when_invalid_value(self):
        parameters = [
            create_script_param_config('p1', type='int'),
            create_script_param_config('dependant', type='list', values_script='echo "${p1}"')
        ]
        config_model = _create_config_model('conf_x', parameters=parameters)

        self.assertRaises(InvalidValueException, config_model.set_param_value, 'p1', 'ABC')

    def test_get_parameter_values_when_replace_correct_with_invalid_value(self):
        parameters = [
            create_script_param_config('p1', type='int'),
            create_script_param_config('dependant', type='list', values_script='echo "${p1}"')
        ]
        config_model = _create_config_model('conf_x', parameters=parameters)
        dependant_parameter = config_model.find_parameter('dependant')

        config_model.set_param_value('p1', 12345)
        self.assertEqual(['12345'], dependant_parameter.values)

        try:
            config_model.set_param_value('p1', 'ABC')
            self.fail('Invalid value was set, this should not be possible')
        except InvalidValueException:
            self.assertEqual([], dependant_parameter.values)

    def test_get_required_parameters(self):
        parameters = [
            create_script_param_config('p1'),
            create_script_param_config('dependant', type='list', values_script='echo "${p1}""${p2}"'),
            create_script_param_config('p2')
        ]
        config_model = _create_config_model('conf_x', parameters=parameters)
        dependant_parameter = config_model.find_parameter('dependant')

        self.assertCountEqual(['p1', 'p2'], dependant_parameter.get_required_parameters())


class ConfigModelIncludeTest(unittest.TestCase):
    def test_static_include_simple(self):
        included_path = test_utils.write_script_config({'script_path': 'ping google.com'}, 'included')
        config_model = _create_config_model('main_conf', config={'include': included_path})

        self.assertEqual('ping google.com', config_model.script_command)

    def test_static_include_precedence(self):
        included_path = test_utils.write_script_config({
            'script_path': 'ping google.com',
            'working_directory': '123'},
            'included')
        config_model = _create_config_model('main_conf', config={
            'include': included_path,
            'working_directory': 'abc'})

        self.assertEqual('abc', config_model.working_directory)

    def test_static_include_single_parameter(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('param2', type='int')
        ]}, 'included')
        config_model = _create_config_model('main_conf', config={
            'include': included_path,
            'parameters': [create_script_param_config('param1', type='text')]})

        self.assertEqual(2, len(config_model.parameters))
        param1 = config_model.parameters[0]
        self.assertEqual('param1', param1.name)
        self.assertEqual('text', param1.type)

        param2 = config_model.parameters[1]
        self.assertEqual('param2', param2.name)
        self.assertEqual('int', param2.type)

    def test_static_include_corrupted_file(self):
        included_path = os.path.join(test_utils.temp_folder, 'file.json')
        file_utils.write_file(included_path, 'Hello world!')

        config_model = _create_config_model('main_conf', config={
            'include': included_path,
            'parameters': [create_script_param_config('param1', type='text')]})

        self.assertEqual(1, len(config_model.parameters))

    def test_static_include_hidden_config(self):
        included_path = test_utils.write_script_config({
            'script_path': 'ping google.com',
            'hidden': True},
            'included')
        config_model = _create_config_model('main_conf', config={'include': included_path})

        self.assertEqual('ping google.com', config_model.script_command)

    def test_static_include_ignore_same_parameter(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('param1', type='int', required=False)
        ]}, 'included')
        config_model = _create_config_model('main_conf', config={
            'include': included_path,
            'parameters': [create_script_param_config('param1', type='text', required=True)]})

        self.assertEqual(1, len(config_model.parameters))
        param1 = config_model.parameters[0]
        self.assertEqual('text', param1.type)
        self.assertEqual(True, param1.required)

    def test_dynamic_include_add_parameter(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param')
        ]}, 'included')
        config_model = _create_config_model('main_conf', config={
            'include': '${p1}',
            'parameters': [create_script_param_config('p1')]})
        config_model.set_param_value('p1', included_path)

        self.assertEqual(2, len(config_model.parameters))
        included_param = config_model.parameters[1]
        self.assertEqual('included_param', included_param.name)

    def test_dynamic_include_remove_parameter(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param')
        ]}, 'included')
        config_model = _create_config_model(
            'main_conf',
            config={
                'include': '${p1}',
                'parameters': [create_script_param_config('p1')]},
            parameter_values={'p1': included_path})

        config_model.set_param_value('p1', '')

        self.assertEqual(1, len(config_model.parameters))
        included_param = config_model.parameters[0]
        self.assertEqual('p1', included_param.name)

    def test_dynamic_include_remove_multiple_parameters(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param1'),
            create_script_param_config('included_param2'),
            create_script_param_config('included_param3')
        ]}, 'included')
        config_model = _create_config_model(
            'main_conf',
            config={
                'include': '${p1}',
                'parameters': [create_script_param_config('p1')]},
            parameter_values={'p1': included_path})

        config_model.set_param_value('p1', '')

        self.assertEqual(1, len(config_model.parameters))
        included_param = config_model.parameters[0]
        self.assertEqual('p1', included_param.name)

    def test_dynamic_include_wrong_path(self):
        config_model = _create_config_model('main_conf', config={
            'include': '${p1}',
            'parameters': [create_script_param_config('p1')]})
        config_model.set_param_value('p1', 'some path')

        self.assertEqual(1, len(config_model.parameters))

    def test_dynamic_include_relative_path(self):
        folder = os.path.join(test_utils.temp_folder, 'inner', 'confs')

        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param')
        ]}, 'included', folder)
        included_folder = os.path.dirname(included_path)
        config_model = _create_config_model(
            'main_conf',
            path=os.path.join(folder, 'mainConf.json'),
            config={
                'include': '${p1}',
                'working_directory': included_folder,
                'parameters': [create_script_param_config('p1')]})
        config_model.set_param_value('p1', 'included.json')

        self.assertEqual(2, len(config_model.parameters))

    def test_dynamic_include_replace(self):
        included_path1 = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param_X')
        ]}, 'included1')

        included_path2 = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param_Y')
        ]}, 'included2')

        config_model = _create_config_model('main_conf', config={
            'include': '${p1}',
            'parameters': [create_script_param_config('p1')]})
        config_model.set_param_value('p1', included_path1)
        config_model.set_param_value('p1', included_path2)

        self.assertEqual(2, len(config_model.parameters))
        self.assertEqual('p1', config_model.parameters[0].name)
        self.assertEqual('included_param_Y', config_model.parameters[1].name)

    def test_dynamic_include_replace_with_missing_file(self):
        included_path1 = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param_X')
        ]}, 'included1')

        config_model = _create_config_model('main_conf', config={
            'include': '${p1}',
            'parameters': [create_script_param_config('p1')]})
        config_model.set_param_value('p1', included_path1)
        config_model.set_param_value('p1', 'a/b/c/some.txt')

        self.assertEqual(1, len(config_model.parameters))
        self.assertEqual('p1', config_model.parameters[0].name)

    def test_set_all_values_for_included(self):
        included_path = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param1'),
            create_script_param_config('included_param2')
        ]}, 'included')
        config_model = _create_config_model(
            'main_conf',
            config={
                'include': '${p1}',
                'parameters': [create_script_param_config('p1')]})

        values = {'p1': included_path, 'included_param1': 'X', 'included_param2': 123}
        config_model.set_all_param_values(values)

        self.assertEqual(values, config_model.parameter_values)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestParametersValidation(unittest.TestCase):
    def test_no_parameters(self):
        script_config = _create_config_model('conf_x')

        valid = self._validate(script_config, {})
        self.assertTrue(valid)

    def test_multiple_required_parameters_when_all_defined(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name, required=True)
            parameters.append(parameter)
            values[param_name] = str(i)

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, values)
        self.assertTrue(valid)

    def test_multiple_required_parameters_when_one_missing(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name, required=True)
            parameters.append(parameter)

            if i != 4:
                values[param_name] = str(i)

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, values)
        self.assertFalse(valid)

    def test_multiple_parameters_when_all_defined(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name)
            parameters.append(parameter)
            values[param_name] = str(i)

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, values)
        self.assertTrue(valid)

    def test_multiple_parameters_when_all_missing(self):
        parameters = []
        for i in range(0, 5):
            parameter = create_script_param_config('param' + str(i))
            parameters.append(parameter)

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, {})
        self.assertTrue(valid)

    def test_multiple_int_parameters_when_all_valid(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name, type='int')
            parameters.append(parameter)
            values[param_name] = i

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, values)
        self.assertTrue(valid)

    def test_multiple_int_parameters_when_one_invalid(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name, type='int')
            parameters.append(parameter)

            if i != 4:
                values[param_name] = i
            else:
                values[param_name] = 'val'

        script_config = _create_config_model('conf_x', parameters=parameters)

        valid = self._validate(script_config, values)
        self.assertFalse(valid)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

    @staticmethod
    def _validate(script_config, parameter_values):
        try:
            script_config.set_all_param_values(parameter_values)
            return True

        except InvalidValueException:
            return False


class TestSingleParameterValidation(unittest.TestCase):

    def test_string_parameter_when_none(self):
        parameter = create_parameter_model('param')

        error = parameter.validate_value(None)
        self.assertIsNone(error)

    def test_string_parameter_when_value(self):
        parameter = create_parameter_model('param')

        error = parameter.validate_value('val')
        self.assertIsNone(error)

    def test_required_parameter_when_none(self):
        parameter = create_parameter_model('param', required=True)

        error = parameter.validate_value({})
        self.assert_error(error)

    def test_required_parameter_when_empty(self):
        parameter = create_parameter_model('param', required=True)

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

    def test_multiselect_when_empty_string(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('')
        self.assertIsNone(error)

    def test_multiselect_when_empty_list(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value([])
        self.assertIsNone(error)

    def test_multiselect_when_single_matching_element(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2'])
        self.assertIsNone(error)

    def test_multiselect_when_multiple_matching_elements(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2', 'val1'])
        self.assertIsNone(error)

    def test_multiselect_when_multiple_elements_one_not_matching(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['val2', 'val1', 'X'])
        self.assert_error(error)

    def test_multiselect_when_not_list_value(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value('val1')
        self.assert_error(error)

    def test_multiselect_when_single_not_matching_element(self):
        parameter = create_parameter_model(
            'param', type='multiselect', allowed_values=['val1', 'val2', 'val3'])

        error = parameter.validate_value(['X'])
        self.assert_error(error)

    def test_list_with_script_when_matches(self):
        parameter = create_parameter_model('param', type=list, values_script="echo '123\n' 'abc'")

        error = parameter.validate_value('abc')
        self.assertIsNone(error)

    def test_list_with_dependency_when_matches(self):
        parameters = []
        values = ObservableDict()
        dep_param = create_parameter_model('dep_param')
        parameter = create_parameter_model('param',
                                           type='list',
                                           values_script="echo '${dep_param}_\n' '_${dep_param}_'",
                                           all_parameters=parameters,
                                           other_param_values=values)
        parameters.extend([dep_param, parameter])

        values['dep_param'] = 'abc'
        error = parameter.validate_value(' _abc_')
        self.assertIsNone(error)

    def assert_error(self, error):
        self.assertFalse(is_blank(error), 'Expected validation error, but validation passed')


class TestTemplateProperty(unittest.TestCase):
    def test_single_parameter(self):
        self.add_parameter(create_parameter_model('param'))
        property = self.create_property('Hello, ${param}!')

        self.set_value('param', 'world')
        self.assertEqual('Hello, world!', property.get())

    def test_single_parameter_when_no_value(self):
        self.add_parameter(create_parameter_model('param'))
        property = self.create_property('Hello, ${param}!')

        self.assertIsNone(property.get())

    def test_single_parameter_with_value_on_init(self):
        self.add_parameter(create_parameter_model('param'))
        self.set_value('param', 'world')
        property = self.create_property('Hello, ${param}!')

        self.assertEqual('Hello, world!', property.get())

    def test_no_dependencies(self):
        self.add_parameter(create_parameter_model('param'))
        property = self.create_property('Test value')

        self.assertEqual('Test value', property.get())

    def test_multiple_parameters(self):
        self.add_parameter(create_parameter_model('p1'))
        self.add_parameter(create_parameter_model('p2'))
        self.add_parameter(create_parameter_model('p3'))

        property = self.create_property('Hello, ${p1}, ${p2} and ${p3}!')

        self.set_value('p1', 'John')
        self.set_value('p2', 'Mary')
        self.set_value('p3', 'world')

        self.assertEqual('Hello, John, Mary and world!', property.get())

    def test_multiple_parameters_when_one_missing(self):
        self.add_parameter(create_parameter_model('p1'))
        self.add_parameter(create_parameter_model('p2'))
        self.add_parameter(create_parameter_model('p3'))

        property = self.create_property('Hello, ${p1}, ${p2} and ${p3}!')

        self.set_value('p1', 'John')
        self.set_value('p3', 'world')

        self.assertIsNone(property.get())

    def test_multiple_parameters_when_one_becomes_missing(self):
        self.add_parameter(create_parameter_model('p1'))
        self.add_parameter(create_parameter_model('p2'))
        self.add_parameter(create_parameter_model('p3'))
        self.set_value('p1', 'John')
        self.set_value('p2', 'Mary')
        self.set_value('p3', 'world')
        property = self.create_property('Hello, ${p1}, ${p2} and ${p3}!')

        self.set_value('p3', None)

        self.assertIsNone(property.get())

    def test_multiple_parameters_when_one_repeats(self):
        self.add_parameter(create_parameter_model('p1'))
        self.add_parameter(create_parameter_model('p2'))
        property = self.create_property('Hello ${p1}, ${p1}, ${p2} and ${p1}!')

        self.set_value('p1', 'John')
        self.set_value('p2', 'Mary')

        self.assertEqual('Hello John, John, Mary and John!', property.get())

    def test_multiple_parameters_get_required(self):
        self.add_parameter(create_parameter_model('p1'))
        self.add_parameter(create_parameter_model('p2'))
        self.add_parameter(create_parameter_model('p3'))
        property = self.create_property('Hello ${p1}, ${p3} and ${p2}!')

        self.assertCountEqual(['p1', 'p2', 'p3'], property.required_parameters)

    def test_value_without_parameter(self):
        self.set_value('p1', 'John')
        property = self.create_property('Hello, ${p1}!')

        self.assertEqual('Hello, ${p1}!', property.get())

    def test_late_add_single_parameter(self):
        self.set_value('p1', 'John')
        property = self.create_property('Hello, ${p1}!')

        self.add_parameter(create_parameter_model('p1'))

        self.assertEqual('Hello, John!', property.get())

    def test_late_remove_single_parameter(self):
        parameter = create_parameter_model('p1')
        self.add_parameter(parameter)
        self.set_value('p1', 'John')
        property = self.create_property('Hello, ${p1}!')

        self.parameters.remove(parameter)

        self.assertEqual('Hello, ${p1}!', property.get())

    def setUp(self):
        super().setUp()

        self.parameters = ObservableList()
        self.values = ObservableDict()

    def create_property(self, template):
        return _TemplateProperty(template, self.parameters, self.values)

    def add_parameter(self, config):
        self.parameters.append(config)

    def set_value(self, name, value):
        self.values[name] = value


def _create_parameter_model(config, *, username=DEF_USERNAME, audit_name=DEF_AUDIT_NAME, all_parameters=None):
    return create_parameter_model_from_config(config,
                                              username=username,
                                              audit_name=audit_name,
                                              all_parameters=all_parameters)


def _create_config_model(name, *,
                         config=None,
                         username=DEF_USERNAME,
                         audit_name=DEF_AUDIT_NAME,
                         path=None,
                         parameters=None,
                         parameter_values=None):
    result_config = {}

    if config:
        result_config.update(config)

    result_config['name'] = name

    if parameters is not None:
        result_config['parameters'] = parameters

    if path is None:
        path = name

    return ConfigModel(result_config, path, username, audit_name, parameter_values=parameter_values)
