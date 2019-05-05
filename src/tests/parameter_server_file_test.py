import os
import stat
import unittest

from config.constants import PARAM_TYPE_SERVER_FILE, FILE_TYPE_FILE, FILE_TYPE_DIR
from model.parameter_config import WrongParameterUsageException
from model.script_config import InvalidValueException
from tests import test_utils
from tests.test_utils import create_script_param_config, create_files


class ServerFileConfigTest(unittest.TestCase):
    def test_create_by_config(self):
        config = test_utils.create_parameter_model_from_config(_create_config())

        self.assertEqual(PARAM_TYPE_SERVER_FILE, config.type)

    def test_create_recursive_by_config(self):
        config = test_utils.create_parameter_model_from_config(_create_config(recursive='true'))

        self.assertEqual(PARAM_TYPE_SERVER_FILE, config.type)
        self.assertEqual(True, config.file_recursive)

    def test_create_config_fails_on_missing_dir(self):
        self.assertRaises(Exception, test_utils.create_parameter_model_from_config,
                          _create_config(''))

    def test_create_when_relative_to_working_dir(self):
        path = os.path.join('my', 'dir')

        config = test_utils.create_parameter_model_from_config(
            _create_config(path),
            working_dir=test_utils.temp_folder)

        self.assertEqual(path, config.file_dir)

    def test_create_when_no_extensions(self):
        config = test_utils.create_parameter_model_from_config(
            _create_config())

        self.assertEqual([], config.file_extensions)

    def test_create_when_unnormalized_extensions(self):
        config = test_utils.create_parameter_model_from_config(
            _create_config(extensions=['.pdf', 'TxT', 'log', '.minE']))

        self.assertEqual(['pdf', 'txt', 'log', 'mine'], config.file_extensions)

    def test_file_type(self):
        config = test_utils.create_parameter_model_from_config(
            _create_config(file_type='DiR'))
        self.assertEqual('dir', config.file_type)

    def test_file_type_dir_overriden_by_extensions(self):
        config = test_utils.create_parameter_model_from_config(
            _create_config(file_type='dir', extensions=['exe']))
        self.assertEqual('file', config.file_type)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class PlainServerFileTest(unittest.TestCase):
    def test_allowed_values(self):
        create_files(['abc', 'xyz', 'def'])
        config = _create_parameter_model(recursive=False)
        self.assertEqual(['abc', 'def', 'xyz'], config.values)

    def test_empty_allowed_values(self):
        config = _create_parameter_model(recursive=False)
        self.assertEqual([], config.values)

    def test_allowed_values_when_working_dir(self):
        working_dir = os.path.join('work', 'dir')
        file_dir = 'inner'
        create_files(['abc', 'def'], os.path.join(working_dir, file_dir))
        working_dir_path = os.path.join(test_utils.temp_folder, working_dir)
        config = _create_parameter_model(recursive=False, file_dir=file_dir, working_dir=working_dir_path)
        self.assertEqual(['abc', 'def'], config.values)

    def test_map_non_empty_value(self):
        filename = 'file1.txt'

        config = _create_parameter_model(recursive=False)
        self.assertEqual(os.path.join(test_utils.temp_folder, filename), config.map_to_script(filename))

    def test_map_empty_value(self):
        config = _create_parameter_model(recursive=False)
        self.assertEqual(None, config.map_to_script(''))

    def test_map_when_working_dir(self):
        working_dir_path = os.path.join(test_utils.temp_folder, 'work', 'dir')
        file_dir = 'inner'
        config = _create_parameter_model(recursive=False, file_dir=file_dir, working_dir=working_dir_path)
        self.assertEqual(os.path.join(file_dir, 'file.txt'), config.map_to_script('file.txt'))

    def test_validate_success_when_working_dir(self):
        working_dir = os.path.join('work', 'dir')
        file_dir = 'inner'
        create_files(['abc', 'def'], os.path.join(working_dir, file_dir))
        working_dir_path = os.path.join(test_utils.temp_folder, 'work', 'dir')
        config = _create_parameter_model(recursive=False, file_dir=file_dir, working_dir=working_dir_path)
        self.assertIsNone(config.validate_value('def'))

    def test_validate_failure_when_working_dir(self):
        file_dir = 'inner'
        create_files(['abc', 'def'], file_dir)
        working_dir_path = os.path.join(test_utils.temp_folder, 'work', 'dir')
        config = _create_parameter_model(recursive=False, file_dir=file_dir, working_dir=working_dir_path)
        self.assertRegex(config.validate_value('def'), '.+ but should be in \[\]')

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class RecursiveServerFileTest(unittest.TestCase):
    def test_empty_allowed_values(self):
        create_files(['abc', 'def'])
        config = _create_parameter_model(recursive=True)
        self.assertEqual(None, config.values)

    def test_list_files_simple(self):
        config = _create_parameter_model(recursive=True)
        create_files(['abc', 'def'])

        files = config.list_files([])
        self.assertCountEqual([_file('abc'), _file('def')], files)

    def test_list_files_with_nested_structure(self):
        config = _create_parameter_model(recursive=True)

        create_files(['abc.txt', 'def.pdf'])
        create_files(['admin.log'], 'hidden')
        create_files(['music.mp3'], 'public')

        files = config.list_files([])
        self.assertCountEqual(
            [_file('abc.txt'),
             _file('def.pdf'),
             _dir('hidden'),
             _dir('public')],
            files)

    def test_list_files_1_level(self):
        config = _create_parameter_model(recursive=True)

        create_files(['abc.txt', 'def.pdf'])
        create_files(['admin.log', 'passwords'], 'hidden')
        create_files(['music.mp3'], 'public')

        files = config.list_files(['hidden'])
        self.assertCountEqual([
            _file('admin.log'),
            _file('passwords')],
            files)

    def test_list_files_3_level(self):
        create_files(['xyz'], os.path.join('my', 'home', 'folder', 'temp'))
        create_files(['abc', 'def'], os.path.join('my', 'home', 'folder'))
        create_files(['music.mp3'], os.path.join('my', 'home'))
        config = _create_parameter_model(recursive=True)

        files = config.list_files(['my', 'home', 'folder'])
        self.assertCountEqual([
            _file('abc'),
            _file('def'),
            _dir('temp')],
            files)

    def test_list_files_unaccessible_dir(self):
        create_files(['file1'], os.path.join('public'))
        create_files(['file2'], os.path.join('private'))
        config = _create_parameter_model(recursive=True)

        private_path = os.path.join(test_utils.temp_folder, 'private')
        os.chmod(private_path, stat.S_IWRITE)

        try:
            files = config.list_files([])
            self.assertCountEqual([
                _dir('public'),
                _dir('private', readable=False)],
                files)
        finally:
            os.chmod(private_path, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)

    def test_list_files_when_file_type_file(self):
        create_files(['abc', 'def'], os.path.join('my_dir'))
        create_files(['xyz', 'nop'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_FILE)

        files = config.list_files([])
        self.assertCountEqual([
            _file('xyz'),
            _file('nop'),
            _dir('my_dir')],
            files)

    def test_list_files_when_file_type_dir(self):
        create_files(['abc', 'def'], os.path.join('my_dir'))
        create_files(['xyz', 'nop'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR)

        files = config.list_files([])
        self.assertCountEqual([
            _dir('my_dir')],
            files)

    def test_list_files_when_extension(self):
        create_files(['xyz', 'nop'], os.path.join('my_dir'))
        create_files(['abc.txt', 'def.pdf'])
        config = _create_parameter_model(recursive=True, extensions=['pdf'])

        files = config.list_files([])
        self.assertCountEqual([
            _file('def.pdf'),
            _dir('my_dir')],
            files)

    def test_list_files_fails_when_wrong_path_type(self):
        create_files(['abc'], 'my_folder')
        config = _create_parameter_model(recursive=True)

        self.assertRaises(InvalidValueException, config.list_files, 'my_folder')

    def test_list_files_fails_when_missing_path(self):
        create_files(['abc'], 'my_folder')
        config = _create_parameter_model(recursive=True)

        self.assertRaises(InvalidValueException, config.list_files, ['home'])

    def test_list_files_fails_when_relative_path(self):
        create_files(['abc'], 'my_folder')
        config = _create_parameter_model(recursive=True)

        self.assertRaises(InvalidValueException, config.list_files, ['.', 'my_folder'])

    def test_list_files_when_folder_with_dot(self):
        create_files(['abc'], '.my_folder')
        config = _create_parameter_model(recursive=True)

        files = config.list_files(['.my_folder'])
        self.assertCountEqual([_file('abc')], files)

    def test_list_files_when_unaccessible_parent(self):
        create_files(['abc'], os.path.join('some', 'nested', 'folder'))
        config = _create_parameter_model(recursive=True)

        protected_dir = os.path.join(test_utils.temp_folder, 'some')
        os.chmod(protected_dir, stat.S_IWRITE)

        try:
            self.assertRaises(InvalidValueException, config.list_files, ['some', 'nested', 'folder'])
        finally:
            os.chmod(protected_dir, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)

    def test_list_files_when_unaccessible_child(self):
        test_path = os.path.join('some', 'nested', 'folder')
        create_files(['abc'], test_path)
        config = _create_parameter_model(recursive=True)

        protected_dir = os.path.join(test_utils.temp_folder, test_path)
        os.chmod(protected_dir, stat.S_IWRITE)

        try:
            self.assertRaises(InvalidValueException, config.list_files, ['some', 'nested', 'folder'])
        finally:
            os.chmod(protected_dir, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)

    def test_list_files_when_not_directory(self):
        create_files(['abc'])
        config = _create_parameter_model(recursive=True)

        self.assertRaises(InvalidValueException, config.list_files, ['abc'])

    def test_list_files_for_nested_when_file_type_and_extensions(self):
        create_files(['abc', 'def'])
        create_files(['xyz.txt', 'def.pdf', 'admin.log'], 'sub')
        create_files(['grandchild.log'], os.path.join('sub', 'logs'))
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_FILE, extensions=['pdf', 'log'])

        files = config.list_files(['sub'])
        self.assertCountEqual([
            _file('def.pdf'),
            _file('admin.log'),
            _dir('logs')],
            files)

    def test_list_files_for_non_recursive(self):
        create_files(['abc', 'def'])
        config = _create_parameter_model(recursive=False)

        self.assertRaises(WrongParameterUsageException, config.list_files, [])

    def test_list_files_when_working_dir(self):
        working_dir = os.path.join('work', 'dir')
        file_dir = 'inner'

        create_files(['xyz', 'abc'], os.path.join(working_dir, file_dir, 'my_dir'))
        working_dir_path = os.path.join(test_utils.temp_folder, working_dir)
        config = _create_parameter_model(recursive=True, file_dir=file_dir, working_dir=working_dir_path)

        files = config.list_files(['my_dir'])
        self.assertCountEqual([_file('xyz'), _file('abc')], files)

    def test_list_files_when_working_dir_and_file_dir_dotdot(self):
        working_dir = os.path.join('work', 'dir')
        create_files(['xyz', 'abc'], os.path.join('work', 'another'))
        working_dir_path = os.path.join(test_utils.temp_folder, working_dir)
        config = _create_parameter_model(recursive=True, file_dir='..', working_dir=working_dir_path)

        files = config.list_files(['another'])
        self.assertCountEqual([_file('xyz'), _file('abc')], files)

    def test_validate_missing_value(self):
        config = _create_parameter_model(recursive=True)

        self.assertIsNone(config.validate_value([]))

    def test_validate_existing_top_file(self):
        create_files(['abc'])
        config = _create_parameter_model(recursive=True)

        self.assertIsNone(config.validate_value(['abc']))

    def test_validate_existing_nested_file(self):
        create_files(['abc.txt'], os.path.join('my', 'nested', 'folder'))
        config = _create_parameter_model(recursive=True)

        self.assertIsNone(config.validate_value(['my', 'nested', 'folder', 'abc.txt']))

    def test_validate_missing_top_file(self):
        config = _create_parameter_model(recursive=True)

        error = config.validate_value(['abc'])
        self.assertRegex(error, '.+ does not exist')

    def test_validate_missing_nested_file(self):
        config = _create_parameter_model(recursive=True)

        error = config.validate_value(['my', 'nested', 'folder', 'abc.txt'])
        self.assertRegex(error, '.+ does not exist')

    def test_validate_fail_when_relative_reference(self):
        create_files(['abc.txt'])
        config = _create_parameter_model(recursive=True)

        error = config.validate_value(['..', test_utils.temp_folder, 'abc.txt'])
        self.assertEqual('Relative path references are not allowed', error)

    def test_validate_success_when_extensions(self):
        create_files(['abc.txt', 'admin.log', 'doc.pdf'], 'home')
        config = _create_parameter_model(recursive=True, extensions='txt')

        self.assertIsNone(config.validate_value(['home', 'abc.txt']))

    def test_validate_fail_when_extensions(self):
        create_files(['abc.txt', 'admin.log', 'doc.pdf'], 'home')
        config = _create_parameter_model(recursive=True, extensions='log')

        error = config.validate_value(['home', 'abc.txt'])
        self.assertRegex(error, '.+ is not allowed')

    def test_validate_success_when_file_type_file(self):
        create_files(['abc.txt', 'admin.log'], 'home')
        create_files(['.passwords'], os.path.join('home', 'private'))
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_FILE)

        self.assertIsNone(config.validate_value(['home', 'abc.txt']))

    def test_validate_fail_when_file_type_file(self):
        create_files(['abc.txt', 'admin.log'], 'home')
        create_files(['.passwords'], os.path.join('home', 'private'))
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_FILE)

        error = config.validate_value(['home', 'private'])
        self.assertRegex(error, '.+ is not allowed')

    def test_validate_success_when_file_type_dir(self):
        create_files(['.passwords'], 'private')
        create_files(['tasks.list'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR)

        self.assertIsNone(config.validate_value(['private']))

    def test_validate_fail_when_file_type_dir(self):
        create_files(['.passwords'], 'private')
        create_files(['tasks.list'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR)

        error = config.validate_value(['tasks.list'])
        self.assertRegex(error, '.+ is not allowed')

    def test_validate_success_when_file_type_dir_and_extensions(self):
        create_files(['.passwords'], 'private')
        create_files(['admin.log', 'file.txt', 'print.pdf'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR, extensions=['txt'])

        self.assertIsNone(config.validate_value(['file.txt']))

    def test_validate_fail_on_dir_when_file_type_dir_and_extensions(self):
        create_files(['.passwords'], 'private')
        create_files(['admin.log', 'file.txt', 'print.pdf'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR, extensions=['txt'])

        error = config.validate_value(['private'])
        self.assertRegex(error, '.+ is not allowed')

    def test_validate_fail_on_extension_when_file_type_dir_and_extensions(self):
        create_files(['.passwords'], 'private')
        create_files(['admin.log', 'file.txt', 'print.pdf'])
        config = _create_parameter_model(recursive=True, file_type=FILE_TYPE_DIR, extensions=['txt'])

        error = config.validate_value(['print.pdf'])
        self.assertRegex(error, '.+ is not allowed')

    def test_normalize_when_list(self):
        config = _create_parameter_model(recursive=True)

        self.assertEqual(['home', 'mine'], config.normalize_user_value(['home', 'mine']))

    def test_normalize_when_string(self):
        config = _create_parameter_model(recursive=True)

        self.assertEqual(['docs'], config.normalize_user_value('docs'))

    def test_normalize_when_none(self):
        config = _create_parameter_model(recursive=True)

        self.assertEqual([], config.normalize_user_value(None))

    def test_map_value_single_path(self):
        config = _create_parameter_model(recursive=True)

        mapped_value = config.map_to_script(['file.txt'])
        self.assertEqual(os.path.join(test_utils.temp_folder, 'file.txt'), mapped_value)

    def test_map_value_nested_path(self):
        config = _create_parameter_model(recursive=True)

        mapped_value = config.map_to_script(['home', 'me', 'file.txt'])
        expected_value = os.path.join(test_utils.temp_folder, 'home', 'me', 'file.txt')
        self.assertEqual(expected_value, mapped_value)

    def test_map_value_empty(self):
        config = _create_parameter_model(recursive=True)

        self.assertIsNone(config.map_to_script([]))

    def test_map_when_working_dir(self):
        working_dir = os.path.join('work', 'dir')
        file_dir = 'inner'

        working_dir_path = os.path.join(test_utils.temp_folder, working_dir)
        config = _create_parameter_model(recursive=True, file_dir=file_dir, working_dir=working_dir_path)

        mapped_value = config.map_to_script(['abc.txt'])
        self.assertEqual(os.path.join(file_dir, 'abc.txt'), mapped_value)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


def _create_config(file_dir=test_utils.temp_folder, recursive=None, extensions=None, file_type=None):
    return create_script_param_config(
        'plain_server_file_X',
        type='server_file',
        file_dir=file_dir,
        file_recursive=recursive,
        file_extensions=extensions,
        file_type=file_type)


def _create_parameter_model(*, recursive, file_type=None, extensions=None, working_dir=None,
                            file_dir=test_utils.temp_folder):
    config = _create_config(file_dir, recursive=recursive, file_type=file_type, extensions=extensions)
    return test_utils.create_parameter_model_from_config(config, working_dir=working_dir)


def _file(name):
    return {'name': name, 'readable': True, 'type': 'file'}


def _dir(name, readable=True):
    return {'name': name, 'readable': readable, 'type': 'dir'}
