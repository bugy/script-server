import os
import unittest

from config.script.list_values import DependantScriptValuesProvider, FilesProvider
from config.constants import FILE_TYPE_FILE, FILE_TYPE_DIR
from tests import test_utils
from tests.test_utils import create_parameter_model
from utils import file_utils


class DependantScriptValuesProviderTest(unittest.TestCase):
    def test_get_required_parameters_when_single_dependency(self):
        values_provider = DependantScriptValuesProvider('ls ${param1}', self.create_parameters_supplier('param1'))
        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    def test_get_required_parameters_when_single_dependency_and_many_params(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters_supplier('param1', 'param2', 'param3'))
        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    def test_get_required_parameters_when_multiple_dependencies(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}/${param2}',
            self.create_parameters_supplier('param1', 'param2', 'param3'))
        self.assertCountEqual(['param1', 'param2'], values_provider.get_required_parameters())

    def test_get_values_when_no_values(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters_supplier('param1'))
        self.assertEqual([], values_provider.get_values({}))

    def test_get_values_when_single_parameter(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters_supplier('param1'))
        self.assertEqual(['_hello world_'], values_provider.get_values({'param1': 'hello world'}))

    def test_get_values_when_multiple_parameters(self):
        files_path = os.path.join(test_utils.temp_folder, 'path1', 'path2')
        for i in range(0, 5):
            file_utils.write_file(os.path.join(files_path, 'f' + str(i) + '.txt'), 'test')

        values_provider = DependantScriptValuesProvider(
            'ls ' + test_utils.temp_folder + '/${param1}/${param2}',
            self.create_parameters_supplier('param1', 'param2'))
        self.assertEqual(['f0.txt', 'f1.txt', 'f2.txt', 'f3.txt', 'f4.txt'],
                         values_provider.get_values({'param1': 'path1', 'param2': 'path2'}))

    def test_get_values_when_parameter_repeats(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_\n' 'test\n' '+${param1}+'",
            self.create_parameters_supplier('param1'))
        self.assertEqual(['_123_', ' test', ' +123+'], values_provider.get_values({'param1': '123'}))

    def test_get_values_when_numeric_parameter(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters_supplier('param1'))
        self.assertEqual(['_123_'], values_provider.get_values({'param1': 123}))

    def test_no_code_injection(self):
        values_provider = DependantScriptValuesProvider(
            "echo ${param1}",
            self.create_parameters_supplier('param1'))
        self.assertEqual(['1 && echo 2'], values_provider.get_values({'param1': '1 && echo 2'}))

    def test_script_fails(self):
        values_provider = DependantScriptValuesProvider(
            "echo2 ${param1}",
            self.create_parameters_supplier('param1'))
        self.assertEqual([], values_provider.get_values({'param1': 'abc'}))

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

    def create_parameters_supplier(self, *param_names):
        result = []

        for param_name in param_names:
            parameter = create_parameter_model(param_name, all_parameters=result)
            parameter.name = param_name
            result.append(parameter)

        return lambda: result


class FilesProviderTest(unittest.TestCase):
    def test_single_file(self):
        test_utils.create_file('my.txt')

        self.assertEqual(['my.txt'], self.read_provider_values())

    def test_multiple_files(self):
        self.create_files(['My.txt', 'file.dat', 'test.sh'])
        test_utils.create_dir('documents')

        self.assertEqual(['documents', 'file.dat', 'My.txt', 'test.sh'], self.read_provider_values())

    def test_multiple_files_non_recursive(self):
        for dir in [None, 'documents', 'smth']:
            for file in ['my.txt', 'file.dat']:
                if dir:
                    test_utils.create_file(os.path.join(dir, dir + '_' + file))
                else:
                    test_utils.create_file(file)

        self.assertEqual(['documents', 'file.dat', 'my.txt', 'smth'], self.read_provider_values())

    def test_file_type_file(self):
        files = ['file1', 'file2']
        self.create_files(files)
        test_utils.create_dir('my_dir')

        self.assertEqual(files, self.read_provider_values(file_type=FILE_TYPE_FILE))

    def test_file_type_dir(self):
        files = ['file1', 'file2']
        self.create_files(files)
        test_utils.create_dir('my_dir')

        self.assertEqual(['my_dir'], self.read_provider_values(file_type=FILE_TYPE_DIR))

    def test_file_extensions(self):
        for extension in ['exe', 'dat', 'txt', 'sh', 'pdf', 'docx']:
            for file in ['file1', 'file2']:
                test_utils.create_file(file + '.' + extension)

            test_utils.create_dir('my_dir' + '.' + extension)

        self.assertEqual(['file1.exe', 'file1.pdf', 'file2.exe', 'file2.pdf'],
                         self.read_provider_values(file_extensions=['exe', '.pdf']))

    def create_files(self, names, dir=None):
        for name in names:
            if dir is not None:
                test_utils.create_file(os.path.join(dir, name))
            else:
                test_utils.create_file(name)

    def read_provider_values(self, file_type=None, file_extensions=None):
        provider = FilesProvider(test_utils.temp_folder, file_type=file_type, file_extensions=file_extensions)
        values = provider.get_values({})
        return values

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()
