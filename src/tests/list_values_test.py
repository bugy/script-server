import os
import unittest

from parameterized import parameterized

from config.script.list_values import DependantScriptValuesProvider, FilesProvider, ScriptValuesProvider
from tests import test_utils
from tests.test_utils import create_parameter_model
from utils import file_utils
from utils.process_utils import ExecutionException


class ScriptValuesProviderTest(unittest.TestCase):
    @parameterized.expand([(True,), (False,)])
    def test_ls_3_files(self, shell):
        test_utils.create_files(['f1', 'f2', 'f3'])
        provider = ScriptValuesProvider('ls "' + test_utils.temp_folder + '"',
                                        shell=shell)
        self.assertEqual(['f1', 'f2', 'f3'], provider.get_values({}))

    @parameterized.expand([(True,), (False,)])
    def test_ls_no_files(self, shell):
        provider = ScriptValuesProvider('ls "' + test_utils.temp_folder + '"',
                                        shell=shell)
        self.assertEqual([], provider.get_values({}))

    def test_ls_3_files_when_bash_operator(self):
        test_utils.create_files(['f1', 'f2', 'f3'])
        self.assertRaises(ExecutionException,
                          ScriptValuesProvider,
                          'ls "' + test_utils.temp_folder + '" | grep 2',
                          shell=False)

    def test_ls_3_files_when_bash_operator_and_shell(self):
        test_utils.create_files(['f1', 'f2', 'f3'])
        provider = ScriptValuesProvider('ls "' + test_utils.temp_folder + '" | grep 2',
                                        shell=True)
        self.assertEqual(['f2'], provider.get_values({}))

    def setUp(self) -> None:
        super().setUp()

        test_utils.setup()

    def tearDown(self) -> None:
        super().tearDown()

        test_utils.cleanup()


class DependantScriptValuesProviderTest(unittest.TestCase):

    @parameterized.expand([(True,), (False,)])
    def test_get_required_parameters_when_single_dependency(self, shell):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters_supplier('param1'),
            shell=shell)

        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    @parameterized.expand([(True,), (False,)])
    def test_get_required_parameters_when_single_dependency_and_many_params(self, shell):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters_supplier('param1', 'param2', 'param3'),
            shell=shell)
        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    @parameterized.expand([(True,), (False,)])
    def test_get_required_parameters_when_multiple_dependencies(self, shell):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}/${param2}',
            self.create_parameters_supplier('param1', 'param2', 'param3'),
            shell=shell)
        self.assertCountEqual(['param1', 'param2'], values_provider.get_required_parameters())

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_no_values(self, shell):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual([], values_provider.get_values({}))

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_single_parameter(self, shell):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual(['_hello world_'], values_provider.get_values({'param1': 'hello world'}))

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_multiple_parameters(self, shell):
        files_path = os.path.join(test_utils.temp_folder, 'path1', 'path2')
        for i in range(0, 5):
            file_utils.write_file(os.path.join(files_path, 'f' + str(i) + '.txt'), 'test')

        values_provider = DependantScriptValuesProvider(
            'ls ' + test_utils.temp_folder + '/${param1}/${param2}',
            self.create_parameters_supplier('param1', 'param2'),
            shell=shell)
        self.assertEqual(['f0.txt', 'f1.txt', 'f2.txt', 'f3.txt', 'f4.txt'],
                         values_provider.get_values({'param1': 'path1', 'param2': 'path2'}))

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_parameter_repeats(self, shell):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_\n' 'test\n' '+${param1}+'",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual(['_123_', ' test', ' +123+'], values_provider.get_values({'param1': '123'}))

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_numeric_parameter(self, shell):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual(['_123_'], values_provider.get_values({'param1': 123}))

    @parameterized.expand([(True,), (False,)])
    def test_get_values_when_newline_response(self, shell):
        values_provider = DependantScriptValuesProvider(
            "ls '${param1}'",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual([], values_provider.get_values({'param1': test_utils.temp_folder}))

    @parameterized.expand([(True, ['1', '2']), (False, ['1 && echo 2'])])
    def test_no_code_injection_for_and_operator(self, shell, expected_values):
        values_provider = DependantScriptValuesProvider(
            "echo ${param1}",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual(expected_values, values_provider.get_values({'param1': '1 && echo 2'}))

    @parameterized.expand([(True, ['y2', 'y3']), (False, [])])
    def test_no_code_injection_for_pipe_operator(self, shell, expected_values):
        test_utils.create_files(['x1', 'y2', 'y3'])

        values_provider = DependantScriptValuesProvider(
            "ls ${param1}",
            self.create_parameters_supplier('param1'),
            shell=shell)
        self.assertEqual(expected_values, values_provider.get_values({'param1': test_utils.temp_folder + ' | grep y'}))

    @parameterized.expand([(True,), (False,)])
    def test_script_fails(self, shell):
        values_provider = DependantScriptValuesProvider(
            "echo2 ${param1}",
            self.create_parameters_supplier('param1'),
            shell=shell)
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
    def test_no_files(self):
        provider = FilesProvider(test_utils.temp_folder)
        self.assertEqual([], provider.get_values({}))

    def test_multiple_files(self):
        test_utils.create_files(['My.txt', 'file.dat', 'test.sh', 'file2.txt'])
        test_utils.create_dir('documents')
        test_utils.create_files(['another.txt'], 'documents')

        provider = FilesProvider(test_utils.temp_folder, file_extensions=['txt'])
        self.assertEqual(['file2.txt', 'My.txt'], provider.get_values({}))

    def test_invalid_file_dir(self):
        provider = FilesProvider('some_missing_folder')
        self.assertEqual([], provider.get_values({}))

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()
