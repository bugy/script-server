import json
import os
import unittest

from auth.authorization import Authorizer, EmptyGroupProvider
from auth.user import User
from config.config_service import ConfigService, ConfigNotAllowedException
from tests import test_utils
from tests.test_utils import AnyUserAuthorizer
from utils import file_utils
from utils.audit_utils import AUTH_USERNAME


class ConfigServiceTest(unittest.TestCase):
    def test_list_configs_when_one(self):
        _create_script_config('conf_x')

        configs = self.config_service.list_configs(self.user)
        self.assertEqual(1, len(configs))
        self.assertEqual('conf_x', configs[0].name)

    def test_list_configs_when_multiple(self):
        _create_script_config('conf_x')
        _create_script_config('conf_y')
        _create_script_config('A B C')

        configs = self.config_service.list_configs(self.user)
        conf_names = [config.name for config in configs]
        self.assertCountEqual(['conf_x', 'conf_y', 'A B C'], conf_names)

    def test_list_configs_when_no(self):
        configs = self.config_service.list_configs(self.user)
        self.assertEqual([], configs)

    def test_list_configs_when_one_broken(self):
        broken_conf_path = _create_script_config('broken')
        file_utils.write_file(broken_conf_path, '{ hello ?')
        _create_script_config('correct')

        configs = self.config_service.list_configs(self.user)
        self.assertEqual(1, len(configs))
        self.assertEqual('correct', configs[0].name)

    def test_list_hidden_config(self):
        _create_script_config('conf_x', hidden=True)

        configs = self.config_service.list_configs(self.user)
        self.assertEqual([], configs)

    def test_load_config(self):
        _create_script_config('conf_x')

        config = self.config_service.create_config_model('conf_x', self.user)
        self.assertIsNotNone(config)
        self.assertEqual('conf_x', config.name)

    def test_load_config_when_not_exists(self):
        _create_script_config('conf_x')

        config = self.config_service.create_config_model('ABC', self.user)
        self.assertIsNone(config)

    def test_load_hidden_config(self):
        _create_script_config('conf_x', hidden=True)

        config = self.config_service.create_config_model('conf_x', self.user)
        self.assertIsNone(config)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def setUp(self):
        super().setUp()
        test_utils.setup()

        self.user = User('ConfigServiceTest', {AUTH_USERNAME: 'ConfigServiceTest'})
        self.config_service = ConfigService(AnyUserAuthorizer(), test_utils.temp_folder)


class ConfigServiceAuthTest(unittest.TestCase):
    def test_list_configs_when_no_constraints(self):
        _create_script_config('a1')
        _create_script_config('c2')

        self.assert_list_configs(self.user1, ['a1', 'c2'])

    def test_list_configs_when_user_allowed(self):
        _create_script_config('a1', allowed_users=['user1'])
        _create_script_config('c2', allowed_users=['user1'])

        self.assert_list_configs(self.user1, ['a1', 'c2'])

    def test_list_configs_when_one_not_allowed(self):
        _create_script_config('a1', allowed_users=['XYZ'])
        _create_script_config('b2')
        _create_script_config('c3', allowed_users=['user1'])

        self.assert_list_configs(self.user1, ['b2', 'c3'])

    def test_list_configs_when_none_allowed(self):
        _create_script_config('a1', allowed_users=['XYZ'])
        _create_script_config('b2', allowed_users=['ABC'])

        self.assert_list_configs(self.user1, [])

    def test_load_config_when_user_allowed(self):
        _create_script_config('my_script', allowed_users=['ABC', 'user1', 'qwerty'])

        config = self.config_service.create_config_model('my_script', self.user1)
        self.assertIsNotNone(config)
        self.assertEqual('my_script', config.name)

    def test_load_config_when_user_not_allowed(self):
        _create_script_config('my_script', allowed_users=['ABC', 'qwerty'])

        self.assertRaises(ConfigNotAllowedException, self.config_service.create_config_model, 'my_script', self.user1)

    def assert_list_configs(self, user, expected_names):
        configs = self.config_service.list_configs(user)
        conf_names = [config.name for config in configs]
        self.assertCountEqual(expected_names, conf_names)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], [], EmptyGroupProvider())
        self.user1 = User('user1', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)


def _create_script_config(filename, *, name=None, allowed_users=None, hidden=None):
    conf_folder = os.path.join(test_utils.temp_folder, 'runners')
    file_path = os.path.join(conf_folder, filename + '.json')

    config = {}
    if name is not None:
        config['name'] = name

    if allowed_users is not None:
        config['allowed_users'] = allowed_users

    if hidden is not None:
        config['hidden'] = hidden

    config_json = json.dumps(config)
    file_utils.write_file(file_path, config_json)
    return file_path

