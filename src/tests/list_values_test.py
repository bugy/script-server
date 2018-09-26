import os
import unittest

from config.script.list_values import DependantScriptValuesProvider
from model.script_configs import Parameter
from tests import test_utils
from utils import file_utils


class DependantScriptValuesProviderTest(unittest.TestCase):
    def test_get_required_parameters_when_single_dependency(self):
        values_provider = DependantScriptValuesProvider('ls ${param1}', self.create_parameters('param1'))
        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    def test_get_required_parameters_when_single_dependency_and_many_params(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters('param1', 'param2', 'param3'))
        self.assertCountEqual(['param1'], values_provider.get_required_parameters())

    def test_get_required_parameters_when_multiple_dependencies(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}/${param2}',
            self.create_parameters('param1', 'param2', 'param3'))
        self.assertCountEqual(['param1', 'param2'], values_provider.get_required_parameters())

    def test_unexisting_parameter(self):
        self.assertRaises(Exception,
                          DependantScriptValuesProvider,
                          'ls ${param1}',
                          self.create_parameters('paramX'))

    def test_get_values_when_no_values(self):
        values_provider = DependantScriptValuesProvider(
            'ls ${param1}',
            self.create_parameters('param1'))
        self.assertEqual([], values_provider.get_values({}))

    def test_get_values_when_single_parameter(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters('param1'))
        self.assertEqual(['_hello world_'], values_provider.get_values({'param1': 'hello world'}))

    def test_get_values_when_multiple_parameters(self):
        files_path = os.path.join(test_utils.temp_folder, 'path1', 'path2')
        for i in range(0, 5):
            file_utils.write_file(os.path.join(files_path, 'f' + str(i) + '.txt'), 'test')

        values_provider = DependantScriptValuesProvider(
            'ls ' + test_utils.temp_folder + '/${param1}/${param2}',
            self.create_parameters('param1', 'param2'))
        self.assertEqual(['f0.txt', 'f1.txt', 'f2.txt', 'f3.txt', 'f4.txt'],
                         values_provider.get_values({'param1': 'path1', 'param2': 'path2'}))

    def test_get_values_when_parameter_repeats(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_\n' 'test\n' '+${param1}+'",
            self.create_parameters('param1'))
        self.assertEqual(['_123_', ' test', ' +123+'], values_provider.get_values({'param1': '123'}))

    def test_get_values_when_numeric_parameter(self):
        values_provider = DependantScriptValuesProvider(
            "echo '_${param1}_'",
            self.create_parameters('param1'))
        self.assertEqual(['_123_'], values_provider.get_values({'param1': 123}))

    def test_no_code_injection(self):
        values_provider = DependantScriptValuesProvider(
            "echo ${param1}",
            self.create_parameters('param1'))
        self.assertEqual(['1 && echo 2'], values_provider.get_values({'param1': '1 && echo 2'}))

    def test_constant_parameter(self):
        parameters = self.create_parameters('param 1')
        parameters[0].constant = True

        self.assertRaises(Exception,
                          DependantScriptValuesProvider,
                          'ls ${param1}',
                          parameters)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()

    def create_parameters(self, *param_names):
        result = []

        for param_name in param_names:
            parameter = Parameter()
            parameter.name = param_name
            result.append(parameter)

        return result
