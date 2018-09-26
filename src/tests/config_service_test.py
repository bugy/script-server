import json
import os
import unittest

from config.config_service import ConfigService, ParameterNotFoundException, InvalidValueException
from tests import test_utils
from utils import file_utils


class ConfigServiceTest(unittest.TestCase):
    def test_load_configs_when_one(self):
        self.create_config('conf_x')

        configs = self.config_service.list_configs()
        self.assertEqual(1, len(configs))
        self.assertEqual('conf_x', configs[0].name)

    def test_load_configs_when_multiple(self):
        self.create_config('conf_x')
        self.create_config('conf_y')
        self.create_config('A B C')

        configs = self.config_service.list_configs()
        conf_names = [config.name for config in configs]
        self.assertCountEqual(['conf_x', 'conf_y', 'A B C'], conf_names)

    def test_load_configs_when_no(self):
        configs = self.config_service.list_configs()
        self.assertEqual([], configs)

    def test_load_configs_when_one_broken(self):
        broken_conf_path = self.create_config('broken')
        file_utils.write_file(broken_conf_path, '{ hello ?')
        self.create_config('correct')

        configs = self.config_service.list_configs()
        self.assertEqual(1, len(configs))
        self.assertEqual('correct', configs[0].name)

    def test_get_parameter_values_simple(self):
        parameters = [
            self.create_parameter('p1'),
            self.create_parameter('dependant', type='list', script="echo '${p1}\n' '_${p1}_\n' '${p1}${p1}\n'")
        ]

        self.create_config('conf_x', parameters=parameters)

        values = self.config_service.get_parameter_values('conf_x', 'dependant', {'p1': 'ABC'})
        self.assertEqual(['ABC', ' _ABC_', ' ABCABC'], values)

    def test_get_parameter_values_cached(self):
        parameters = [
            self.create_parameter('p1'),
            self.create_parameter('dependant', type='list', script='echo "${p1}"')
        ]
        config_path = self.create_config('conf_x', parameters=parameters)
        self.config_service.load_config('conf_x')

        file_utils.write_file(config_path, '{}')

        values = self.config_service.get_parameter_values('conf_x', 'dependant', {'p1': 'ABC'})
        self.assertEqual(['ABC'], values)

    def test_get_parameter_values_when_wrong_parameter(self):
        parameters = [
            self.create_parameter('p1'),
            self.create_parameter('dependant', type='list', script='echo "${p1}"')
        ]
        self.create_config('conf_x', parameters=parameters)

        self.assertRaises(ParameterNotFoundException,
                          self.config_service.get_parameter_values,
                          'conf_x', 'p2', {'p1': 'ABC'})

    def test_get_parameter_values_when_invalid_value(self):
        parameters = [
            self.create_parameter('p1', type='int'),
            self.create_parameter('dependant', type='list', script='echo "${p1}"')
        ]
        self.create_config('conf_x', parameters=parameters)

        self.assertRaises(InvalidValueException,
                          self.config_service.get_parameter_values,
                          'conf_x', 'dependant', {'p1': 'ABC'})

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def setUp(self):
        super().setUp()
        test_utils.setup()
        self.config_service = ConfigService(test_utils.temp_folder)

    def create_config(self, filename, *, name=None, parameters=None):
        conf_folder = os.path.join(test_utils.temp_folder, 'runners')
        file_path = os.path.join(conf_folder, filename + '.json')

        config = {}
        if name is not None:
            config['name'] = name

        if parameters is not None:
            config['parameters'] = parameters

        config_json = json.dumps(config)
        file_utils.write_file(file_path, config_json)
        return file_path

    def create_parameter(self, param_name, *, type=None, script=None):
        conf = {'name': param_name}
        if type is not None:
            conf['type'] = type

        if script is not None:
            conf['values'] = {'script': script}

        return conf
