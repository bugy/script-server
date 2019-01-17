import os
import unittest

from config.constants import PARAM_TYPE_MULTISELECT, FILE_TYPE_FILE, FILE_TYPE_DIR
from model import script_configs, model_helper
from model.model_helper import read_list, read_dict, normalize_incoming_values, fill_parameter_values, resolve_env_vars, \
    InvalidFileException
from tests import test_utils
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


class TestNormalizeIncomingValues(unittest.TestCase):

    def test_no_values(self):
        normalized = normalize_incoming_values({}, [])

        self.assertEqual({}, normalized)

    def test_normalize_simple_parameters(self):
        p1 = create_parameter_model('p1')
        p2 = create_parameter_model('p2')
        p3 = create_parameter_model('p3')

        normalized = normalize_incoming_values({'p1': 1, 'p3': None}, [p1, p2, p3])

        self.assertEqual({'p1': 1, 'p3': None}, normalized)

    def test_normalize_one_multiselect(self):
        p1 = create_parameter_model('p1')
        p2 = create_parameter_model('p2', type=PARAM_TYPE_MULTISELECT, allowed_values=['abc'])
        p3 = create_parameter_model('p3')

        normalized = normalize_incoming_values({'p2': 'abc', 'p3': True}, [p1, p2, p3])

        self.assertEqual({'p2': ['abc'], 'p3': True}, normalized)


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

    def __init__(self, *args):
        super().__init__(*args)

        self.original_env = {}

    def test_replace_full_match(self):
        self.set_env_value('my_key', 'my_password')
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
        self.set_env_value('my_key', 'my_password')
        resolved_val = resolve_env_vars('$$my_key')
        self.assertEqual('my_password', resolved_val)

    def test_replace_any_when_single_in_middle(self):
        self.set_env_value('my_key', 'my_password')
        resolved_val = resolve_env_vars('start/$$my_key/end')
        self.assertEqual('start/my_password/end', resolved_val)

    def test_replace_any_when_repeating(self):
        self.set_env_value('my_key', 'abc')
        resolved_val = resolve_env_vars('$$my_key,$$my_key.$$my_key')
        self.assertEqual('abc,abc.abc', resolved_val)

    def test_replace_any_when_multiple(self):
        self.set_env_value('key1', 'Hello')
        self.set_env_value('key2', 'world')
        self.set_env_value('key3', '!')
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

    def set_env_value(self, key, value):
        if key not in self.original_env:
            if key in os.environ:
                self.original_env[key] = value
            else:
                self.original_env[key] = None

        os.environ[key] = value

    def tearDown(self):
        super().tearDown()

        for key, value in self.original_env.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value


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
