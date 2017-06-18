import unittest

import server
from model import model_helper
from model import script_configs


class TestBuildCommandArgs(unittest.TestCase):
    def test_no_parameters_no_values(self):
        config = script_configs.Config()

        args_string = server.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_no_parameters_some_values(self):
        config = script_configs.Config()

        args_string = server.build_command_args({'p1': 'value', 'p2': 'value'}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_no_values(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        config.add_parameter(parameter)

        args_string = server.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_one_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['value'])

    def test_one_parameter_with_param(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['-p1', 'value'])

    def test_one_parameter_flag_no_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = server.build_command_args({}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_flag_false(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': False}, config)

        self.assertEqual(args_string, [])

    def test_one_parameter_flag_true(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '--flag'
        parameter.no_value = True
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': True}, config)

        self.assertEqual(args_string, ['--flag'])

    def test_parameter_constant(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.constant = True
        parameter.default = 'const'
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': 'value'}, config)

        self.assertEqual(args_string, ['const'])

    def test_parameter_int(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.type = 'int'
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': 5}, config)

        self.assertEqual(args_string, ['-p1', 5])

    def test_multiple_parameters_sequence(self):
        config = script_configs.Config()

        p1 = script_configs.Parameter()
        p1.name = 'p1'
        p1.param = '-p1'
        config.add_parameter(p1)

        p2 = script_configs.Parameter()
        p2.name = 'p2'
        config.add_parameter(p2)

        p3 = script_configs.Parameter()
        p3.name = 'p3'
        p3.param = '--p3'
        p3.no_value = True
        config.add_parameter(p3)

        p4 = script_configs.Parameter()
        p4.name = 'p4'
        p4.param = '-p4'
        config.add_parameter(p4)

        p5 = script_configs.Parameter()
        p5.name = 'p5'
        config.add_parameter(p5)

        args_string = server.build_command_args({
            'p1': 'val1',
            'p2': 'val2',
            'p3': 'true',
            'p5': 'val5'},
            config)

        self.assertEqual(args_string, ['-p1', 'val1', 'val2', '--p3', 'val5'])

    def test_parameter_secure_no_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        config.add_parameter(parameter)

        args_string = server.build_command_args({}, config, model_helper.value_to_str)

        self.assertEqual(args_string, [])

    def test_parameter_secure_some_value(self):
        config = script_configs.Config()

        parameter = script_configs.Parameter()
        parameter.name = 'p1'
        parameter.param = '-p1'
        parameter.secure = True
        config.add_parameter(parameter)

        args_string = server.build_command_args({'p1': 'value'}, config, model_helper.value_to_str)

        self.assertEqual(args_string, ['-p1', '******'])
