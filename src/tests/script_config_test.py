import os
import unittest
from collections import OrderedDict

from parameterized import parameterized

from config.constants import PARAM_TYPE_SERVER_FILE, PARAM_TYPE_MULTISELECT
from config.exceptions import InvalidConfigException
from model.script_config import ConfigModel, InvalidValueException, _TemplateProperty, ParameterNotFoundException, \
    get_sorted_config
from react.properties import ObservableDict, ObservableList
from tests import test_utils
from tests.test_utils import create_script_param_config, create_parameter_model, create_files
from utils import file_utils, custom_json

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
        output_format = 'terminal'
        output_files = ['file1', 'file2']

        config_model = _create_config_model(name, config={
            'script_path': script_path,
            'description': description,
            'working_directory': working_directory,
            'requires_terminal': requires_terminal,
            'output_format': output_format,
            'output_files': output_files,
            'scheduling': {'enabled': True}})

        self.assertEqual(name, config_model.name)
        self.assertEqual(script_path, config_model.script_command)
        self.assertEqual(description, config_model.description)
        self.assertEqual(working_directory, config_model.working_directory)
        self.assertEqual(requires_terminal, config_model.requires_terminal)
        self.assertEqual(output_format, config_model.output_format)
        self.assertEqual(output_files, config_model.output_files)
        self.assertTrue(config_model.schedulable)

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

    @parameterized.expand([
        ('html', 'html'),
        ('terminal', 'terminal'),
        ('', 'terminal'),
        ('HTML_iframe', 'html_iframe'),
        (' Text  ', 'text'),
    ])
    def test_create_with_output_format(self, output_format, expected_output_format):
        name = 'conf_y'

        config_model = _create_config_model(name, config={
            'output_format': output_format})

        self.assertEqual(expected_output_format, config_model.output_format)

    def test_create_with_wrong_output_format(self):
        name = 'conf_y'

        self.assertRaisesRegex(InvalidConfigException, 'Invalid output format', _create_config_model, name, config={
            'output_format': 'abc'})


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

    def test_set_all_values_with_normalization(self):
        allowed_values = ['abc', 'def', 'xyz']
        parameters = [
            create_script_param_config('p1', type=PARAM_TYPE_MULTISELECT, allowed_values=allowed_values),
            create_script_param_config('p2', type=PARAM_TYPE_MULTISELECT, allowed_values=allowed_values),
            create_script_param_config('p3', type=PARAM_TYPE_MULTISELECT, allowed_values=allowed_values)]

        config_model = _create_config_model('config', parameters=parameters)
        config_model.set_all_param_values({'p1': '', 'p2': ['def'], 'p3': 'abc'})

        self.assertEqual({'p1': [], 'p2': ['def'], 'p3': ['abc']}, config_model.parameter_values)


class ConfigModelListFilesTest(unittest.TestCase):
    def test_list_files_for_valid_param(self):
        param = create_script_param_config('recurs_file',
                                           type=PARAM_TYPE_SERVER_FILE,
                                           file_recursive=True,
                                           file_dir=test_utils.temp_folder)
        config_model = _create_config_model('my_conf', parameters=[param])

        create_files(['file1', 'file2'])
        file_names = [f['name'] for f in (config_model.list_files_for_param('recurs_file', []))]
        self.assertCountEqual(['file1', 'file2'], file_names)

    def test_list_files_when_working_dir(self):
        param = create_script_param_config('recurs_file',
                                           type=PARAM_TYPE_SERVER_FILE,
                                           file_recursive=True,
                                           file_dir='.')
        config_model = _create_config_model('my_conf', parameters=[param], working_dir=test_utils.temp_folder)

        create_files(['file1', 'file2'])
        file_names = [f['name'] for f in (config_model.list_files_for_param('recurs_file', []))]
        self.assertCountEqual(['file1', 'file2'], file_names)

    def test_list_files_when_unknown_param(self):
        config_model = _create_config_model('my_conf', parameters=[], working_dir=test_utils.temp_folder)

        self.assertRaises(ParameterNotFoundException, config_model.list_files_for_param, 'recurs_file', [])

    def setUp(self):
        super().setUp()
        test_utils.setup()

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()


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
        config_model = _create_config_model('main_conf', script_path=None, config={'include': included_path})

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
        config_model = _create_config_model('main_conf', script_path=None, config={'include': included_path})

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
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param')
        ], 'p1')

        self.assertEqual(2, len(config_model.parameters))
        included_param = config_model.parameters[1]
        self.assertEqual('included_param', included_param.name)

    def test_dynamic_include_remove_parameter(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param')
        ], 'p1')

        config_model.set_param_value('p1', '')

        self.assertEqual(1, len(config_model.parameters))
        included_param = config_model.parameters[0]
        self.assertEqual('p1', included_param.name)

    def test_dynamic_include_remove_multiple_parameters(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param1'),
            create_script_param_config('included_param2'),
            create_script_param_config('included_param3')
        ], 'p1')

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
        (config_model, included_path1) = self.prepare_config_model_with_included([
            create_script_param_config('included_param_X')
        ], 'p1')

        included_path2 = test_utils.write_script_config({'parameters': [
            create_script_param_config('included_param_Y')
        ]}, 'included2')

        config_model.set_param_value('p1', included_path2)

        self.assertEqual(2, len(config_model.parameters))
        self.assertEqual('p1', config_model.parameters[0].name)
        self.assertEqual('included_param_Y', config_model.parameters[1].name)

    def test_dynamic_include_replace_with_missing_file(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param_X')
        ], 'p1')

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

    def test_dynamic_include_add_parameter_with_default(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param', default='abc 123')
        ], 'p1')

        self.assertEqual('abc 123', config_model.parameter_values.get('included_param'))

    def test_dynamic_include_add_parameter_with_default_when_value_exist(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param', default='abc 123')
        ], 'p1')
        config_model.set_param_value('p1', included_path)
        config_model.set_param_value('included_param', 'def 456')

        config_model.set_param_value('p1', 'random value')
        self.assertEqual('def 456', config_model.parameter_values.get('included_param'))

        config_model.set_param_value('p1', included_path)
        self.assertEqual('def 456', config_model.parameter_values.get('included_param'))

    def test_dynamic_include_add_2_parameters_with_default_when_one_dependant(self):
        (config_model, included_path) = self.prepare_config_model_with_included([
            create_script_param_config('included_param1', default='ABC'),
            create_script_param_config('included_param2', default='xABCx', type='list',
                                       values_script='echo x${included_param1}x'),
        ], 'p1')

        self.assertEqual('ABC', config_model.parameter_values.get('included_param1'))
        self.assertEqual('xABCx', config_model.parameter_values.get('included_param2'))

        dependant_parameter = config_model.find_parameter('included_param2')
        self.assertEqual(['xABCx'], dependant_parameter.values)

    def prepare_config_model_with_included(self, included_params, static_param_name):
        included_path = test_utils.write_script_config({'parameters': included_params}, 'included')
        config_model = _create_config_model('main_conf', config={
            'include': '${' + static_param_name + '}',
            'parameters': [create_script_param_config(static_param_name)]})
        config_model.set_param_value(static_param_name, included_path)

        return (config_model, included_path)

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

    def test_multiple_required_parameters_when_one_missing_and_skip_invalid(self):
        values = {}
        parameters = []
        for i in range(0, 5):
            param_name = 'param' + str(i)
            parameter = create_script_param_config(param_name, required=True)
            parameters.append(parameter)

            if i != 3:
                values[param_name] = str(i)

        script_config = _create_config_model('conf_x', parameters=parameters, skip_invalid_parameters=True)

        valid = self._validate(script_config, values, skip_invalid_parameters=True)
        self.assertTrue(valid)
        self.assertEqual({
            'param0': '0',
            'param1': '1',
            'param2': '2',
            'param3': None,
            'param4': '4'},
            script_config.parameter_values)

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
    def _validate(script_config, parameter_values, skip_invalid_parameters=False):
        try:
            script_config.set_all_param_values(parameter_values, skip_invalid_parameters=skip_invalid_parameters)
            return True

        except InvalidValueException:
            return False


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


class GetSortedConfigTest(unittest.TestCase):
    def test_get_sorted_when_3_fields(self):
        config = get_sorted_config({'script_path': 'cd ~', 'name': 'Conf X', 'description': 'My wonderful script'})

        expected = OrderedDict(
            [('name', 'Conf X'),
             ('script_path', 'cd ~'),
             ('description', 'My wonderful script')])
        self.assertEqual(expected, config)

    def test_get_sorted_when_many_fields(self):
        config = get_sorted_config({
            'output_files': ['~/my/file'],
            'name': 'Conf X',
            'include': 'included',
            'parameters': [],
            'description': 'My wonderful script',
            'requires_terminal': False,
            'allowed_users': [],
            'script_path': 'cd ~',
            'working_directory': '~'})

        expected = OrderedDict([
            ('name', 'Conf X'),
            ('script_path', 'cd ~'),
            ('working_directory', '~'),
            ('description', 'My wonderful script'),
            ('allowed_users', []),
            ('include', 'included'),
            ('output_files', ['~/my/file']),
            ('requires_terminal', False),
            ('parameters', []),
        ])
        self.assertEqual(expected, config)

    def test_get_sorted_when_unknown_fields(self):
        config = get_sorted_config({
            'parameters': [],
            'key1': 'abc',
            'requires_terminal': False,
            'key2': 123})

        expected = OrderedDict([
            ('requires_terminal', False),
            ('key1', 'abc'),
            ('key2', 123),
            ('parameters', []),
        ])
        self.assertEqual(expected.popitem(False), config.popitem(False))
        self.assertEqual(expected.popitem(True), config.popitem(True))
        self.assertCountEqual(expected.items(), config.items())

    def test_get_sorted_with_parameters(self):
        config = get_sorted_config({
            'parameters': [{'name': 'param2', 'description': 'desc 1'},
                           {'type': 'int', 'name': 'paramA'},
                           {'default': 'false', 'name': 'param1', 'no_value': True}],
            'name': 'Conf X'})

        expected = OrderedDict([
            ('name', 'Conf X'),
            ('parameters', [
                OrderedDict([('name', 'param2'), ('description', 'desc 1')]),
                OrderedDict([('name', 'paramA'), ('type', 'int')]),
                OrderedDict([('name', 'param1'), ('no_value', True), ('default', 'false')])
            ]),
        ])
        self.assertEqual(expected, config)


    def test_json_comments(self):
        config = get_sorted_config(custom_json.loads(
                """{
                // Comment 1
                "parameters": [
                            // Comment 2
                            {"name": "param2", "description": "desc 1"},
                            {"type": "int", "name": "paramA"},
                            {"default": "false", "name": "param1", "no_value": true}
                            ],
                // Comment 3
                "name": "Conf X"
                }""")
            )

        expected = OrderedDict([
            ('name', 'Conf X'),
            ('parameters', [
                OrderedDict([('name', 'param2'), ('description', 'desc 1')]),
                OrderedDict([('name', 'paramA'), ('type', 'int')]),
                OrderedDict([('name', 'param1'), ('no_value', True), ('default', 'false')])
            ]),
        ])
        self.assertEqual(expected, config)


class SchedulableConfigTest(unittest.TestCase):
    def test_create_with_schedulable_false(self):
        config_model = _create_config_model('some-name', config={
            'scheduling': {'enabled': False}})
        self.assertFalse(config_model.schedulable)

    def test_create_with_schedulable_default(self):
        config_model = _create_config_model('some-name', config={})
        self.assertFalse(config_model.schedulable)

    def test_create_with_schedulable_true_and_secure_parameter(self):
        config_model = _create_config_model('some-name', config={
            'scheduling': {'enabled': True},
            'parameters': [{'name': 'p1', 'secure': True}]
        })
        self.assertFalse(config_model.schedulable)

    def test_create_with_schedulable_true_and_included_secure_parameter(self):
        config_model = _create_config_model('some-name', config={
            'scheduling': {'enabled': True},
            'include': '${p1}',
            'parameters': [{'name': 'p1', 'secure': False}]
        })
        another_path = test_utils.write_script_config(
            {'parameters': [{'name': 'p2', 'secure': True}]},
            'another_config')

        self.assertTrue(config_model.schedulable)

        config_model.set_param_value('p1', another_path)

        self.assertFalse(config_model.schedulable)

    def tearDown(self) -> None:
        test_utils.cleanup()


def _create_config_model(name, *,
                         config=None,
                         username=DEF_USERNAME,
                         audit_name=DEF_AUDIT_NAME,
                         path=None,
                         parameters=None,
                         parameter_values=None,
                         working_dir=None,
                         script_path='echo 123',
                         skip_invalid_parameters=False):
    result_config = {}

    if script_path is not None:
        result_config['script_path'] = script_path

    if config:
        result_config.update(config)

    result_config['name'] = name

    if parameters is not None:
        result_config['parameters'] = parameters

    if path is None:
        path = name

    if working_dir is not None:
        result_config['working_directory'] = working_dir

    model = ConfigModel(result_config, path, username, audit_name)
    if parameter_values is not None:
        model.set_all_param_values(parameter_values, skip_invalid_parameters=skip_invalid_parameters)

    return model
