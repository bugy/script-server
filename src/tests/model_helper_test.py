import os
import unittest

from config.constants import FILE_TYPE_FILE, FILE_TYPE_DIR
from model import model_helper
from model.model_helper import read_list, read_dict, fill_parameter_values, resolve_env_vars, \
    InvalidFileException, read_bool_from_config, InvalidValueException, InvalidValueTypeException
from tests import test_utils
from tests.test_utils import create_parameter_model, set_env_value


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


class TestReadBoolFromConfig(unittest.TestCase):

    def test_bool_true(self):
        value = read_bool_from_config('my_bool', {'my_bool': True})
        self.assertEqual(True, value)

    def test_bool_false(self):
        value = read_bool_from_config('my_bool', {'my_bool': False})
        self.assertEqual(False, value)

    def test_str_true(self):
        value = read_bool_from_config('my_bool', {'my_bool': 'true'})
        self.assertEqual(True, value)

    def test_str_false(self):
        value = read_bool_from_config('my_bool', {'my_bool': 'false'})
        self.assertEqual(False, value)

    def test_str_true_ignore_case(self):
        value = read_bool_from_config('my_bool', {'my_bool': 'TRUE'})
        self.assertEqual(True, value)

    def test_str_false_ignore_case(self):
        value = read_bool_from_config('my_bool', {'my_bool': 'False'})
        self.assertEqual(False, value)

    def test_missing_value_without_default(self):
        value = read_bool_from_config('my_bool', {'text': '123'})
        self.assertIsNone(value)

    def test_missing_value_with_default(self):
        value = read_bool_from_config('my_bool', {'text': '123'}, default=True)
        self.assertEqual(True, value)

    def test_unsupported_type(self):
        self.assertRaisesRegex(
            Exception, '"my_bool" field should be true or false',
            read_bool_from_config,
            'my_bool',
            {'my_bool': 1})


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


class TestResolveEnvVars(unittest.TestCase):

    def test_replace_full_match(self):
        set_env_value('my_key', 'my_password')
        resolved_val = resolve_env_vars('$$my_key', full_match=True)
        self.assertEqual('my_password', resolved_val)

    def test_missing_env_full_match(self):
        self.assertRaises(Exception, resolve_env_vars, '$$my_key', True)

    def test_no_replace_full_match(self):
        value = 'abc!@#$%^&*,?$xyz'
        resolved_val = resolve_env_vars(value, full_match=True)
        self.assertEqual(value, resolved_val)

    def test_no_replace_in_middle_full_match(self):
        value = 'abc$$HOME.123'
        resolved_val = resolve_env_vars(value, full_match=True)
        self.assertEqual(value, resolved_val)

    def test_replace_any_when_exact(self):
        set_env_value('my_key', 'my_password')
        resolved_val = resolve_env_vars('$$my_key')
        self.assertEqual('my_password', resolved_val)

    def test_replace_any_when_single_in_middle(self):
        set_env_value('my_key', 'my_password')
        resolved_val = resolve_env_vars('start/$$my_key/end')
        self.assertEqual('start/my_password/end', resolved_val)

    def test_replace_any_when_repeating(self):
        set_env_value('my_key', 'abc')
        resolved_val = resolve_env_vars('$$my_key,$$my_key.$$my_key')
        self.assertEqual('abc,abc.abc', resolved_val)

    def test_replace_any_when_multiple(self):
        set_env_value('key1', 'Hello')
        set_env_value('key2', 'world')
        set_env_value('key3', '!')
        resolved_val = resolve_env_vars('$$key1 $$key2!$$key3')
        self.assertEqual('Hello world!!', resolved_val)

    def test_replace_any_when_no_env(self):
        resolved_val = resolve_env_vars('Hello $$key1!')
        self.assertEqual('Hello $$key1!', resolved_val)

    def test_resolve_when_empty(self):
        resolved_val = resolve_env_vars('')
        self.assertEqual('', resolved_val)

    def test_resolve_when_int(self):
        resolved_val = resolve_env_vars(123)
        self.assertEqual(123, resolved_val)

    def tearDown(self):
        super().tearDown()

        test_utils.cleanup()


class ListFilesTest(unittest.TestCase):
    def test_single_file(self):
        test_utils.create_file('my.txt')

        files = model_helper.list_files(test_utils.temp_folder)
        self.assertEqual(['my.txt'], files)

    def test_multiple_files(self):
        test_utils.create_files(['My.txt', 'file.dat', 'test.sh'])
        test_utils.create_dir('documents')

        files = model_helper.list_files(test_utils.temp_folder)
        self.assertEqual(['documents', 'file.dat', 'My.txt', 'test.sh'], files)

    def test_multiple_files_non_recursive(self):
        for dir in [None, 'documents', 'smth']:
            for file in ['my.txt', 'file.dat']:
                if dir:
                    test_utils.create_file(os.path.join(dir, dir + '_' + file))
                else:
                    test_utils.create_file(file)

        files = model_helper.list_files(test_utils.temp_folder)
        self.assertEqual(['documents', 'file.dat', 'my.txt', 'smth'], files)

    def test_file_type_file(self):
        files = ['file1', 'file2']
        test_utils.create_files(files)
        test_utils.create_dir('my_dir')

        actual_files = model_helper.list_files(test_utils.temp_folder, file_type=FILE_TYPE_FILE)
        self.assertEqual(files, actual_files)

    def test_file_type_dir(self):
        files = ['file1', 'file2']
        test_utils.create_files(files)
        test_utils.create_dir('my_dir')

        actual_files = model_helper.list_files(test_utils.temp_folder, file_type=FILE_TYPE_DIR)
        self.assertEqual(['my_dir'], actual_files)

    def test_file_extensions(self):
        for extension in ['exe', 'dat', 'txt', 'sh', 'pdf', 'docx']:
            for file in ['file1', 'file2']:
                test_utils.create_file(file + '.' + extension)

            test_utils.create_dir('my_dir' + '.' + extension)

        files = model_helper.list_files(test_utils.temp_folder, file_extensions=['exe', 'pdf'])
        self.assertEqual(['file1.exe', 'file1.pdf', 'file2.exe', 'file2.pdf'], files)

    def test_dir_not_exists(self):
        dir = os.path.join(test_utils.temp_folder, 'dir2')
        self.assertRaises(InvalidFileException, model_helper.list_files, dir)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestReadIntFromConfig(unittest.TestCase):
    def test_normal_int_value(self):
        value = model_helper.read_int_from_config('abc', {'abc': 123})
        self.assertEqual(123, value)

    def test_zero_int_value(self):
        value = model_helper.read_int_from_config('abc', {'abc': 0})
        self.assertEqual(0, value)

    def test_string_value(self):
        value = model_helper.read_int_from_config('abc', {'abc': '-666'})
        self.assertEqual(-666, value)

    def test_string_value_when_invalid(self):
        self.assertRaises(InvalidValueException, model_helper.read_int_from_config, 'abc', {'abc': '1000b'})

    def test_unsupported_type(self):
        self.assertRaises(InvalidValueTypeException, model_helper.read_int_from_config, 'abc', {'abc': True})

    def test_default_value(self):
        value = model_helper.read_int_from_config('my_key', {'abc': 100})
        self.assertIsNone(value)

    def test_default_value_explicit(self):
        value = model_helper.read_int_from_config('my_key', {'abc': 100}, default=5)
        self.assertEqual(5, value)

    def test_default_value_when_empty_string(self):
        value = model_helper.read_int_from_config('my_key', {'my_key': ' '}, default=9999)
        self.assertEqual(9999, value)
