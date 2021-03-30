import json
import os
import unittest
from collections import OrderedDict

from auth.authorization import Authorizer, EmptyGroupProvider
from auth.user import User
from config.config_service import ConfigService, ConfigNotAllowedException, AdminAccessRequiredException
from config.exceptions import InvalidConfigException
from model.model_helper import InvalidFileException
from tests import test_utils
from tests.test_utils import AnyUserAuthorizer
from utils import file_utils
from utils.audit_utils import AUTH_USERNAME
import utils.custom_json as custom_json


class ConfigServiceTest(unittest.TestCase):
    def test_list_configs_when_one(self):
        _create_script_config_file('conf_x')

        configs = self.config_service.list_configs(self.user)
        self.assertEqual(1, len(configs))
        self.assertEqual('conf_x', configs[0].name)

    def test_list_configs_when_multiple(self):
        _create_script_config_file('conf_x')
        _create_script_config_file('conf_y')
        _create_script_config_file('A B C')

        configs = self.config_service.list_configs(self.user)
        conf_names = [config.name for config in configs]
        self.assertCountEqual(['conf_x', 'conf_y', 'A B C'], conf_names)

    def test_list_configs_with_groups(self):
        _create_script_config_file('conf_x', group='g1')
        _create_script_config_file('conf_y')
        _create_script_config_file('A B C', group=' ')

        configs = self.config_service.list_configs(self.user)
        configs_dicts = [{'name': c.name, 'group': c.group} for c in configs]
        self.assertCountEqual([
            {'name': 'conf_x', 'group': 'g1'},
            {'name': 'conf_y', 'group': None},
            {'name': 'A B C', 'group': None}],
            configs_dicts)

    def test_list_configs_when_no(self):
        configs = self.config_service.list_configs(self.user)
        self.assertEqual([], configs)

    def test_list_configs_when_one_broken(self):
        broken_conf_path = _create_script_config_file('broken')
        file_utils.write_file(broken_conf_path, '{ hello ?')
        _create_script_config_file('correct')

        configs = self.config_service.list_configs(self.user)
        self.assertEqual(1, len(configs))
        self.assertEqual('correct', configs[0].name)

    def test_list_hidden_config(self):
        _create_script_config_file('conf_x', hidden=True)

        configs = self.config_service.list_configs(self.user)
        self.assertEqual([], configs)

    def test_load_config(self):
        _create_script_config_file('conf_x')

        config = self.config_service.load_config_model('conf_x', self.user)
        self.assertIsNotNone(config)
        self.assertEqual('conf_x', config.name)

    def test_load_config_when_not_exists(self):
        _create_script_config_file('conf_x')

        config = self.config_service.load_config_model('ABC', self.user)
        self.assertIsNone(config)

    def test_load_hidden_config(self):
        _create_script_config_file('conf_x', hidden=True)

        config = self.config_service.load_config_model('conf_x', self.user)
        self.assertIsNone(config)

    def test_load_config_with_slash_in_name(self):
        _create_script_config_file('conf_x', name='Name with slash /')

        config = self.config_service.load_config_model('Name with slash /', self.user)
        self.assertEquals('Name with slash /', config.name)

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
        _create_script_config_file('a1')
        _create_script_config_file('c2')

        self.assert_list_config_names(self.user1, ['a1', 'c2'])

    def test_list_configs_when_user_allowed(self):
        _create_script_config_file('a1', allowed_users=['user1'])
        _create_script_config_file('c2', allowed_users=['user1'])

        self.assert_list_config_names(self.user1, ['a1', 'c2'])

    def test_list_configs_when_one_not_allowed(self):
        _create_script_config_file('a1', allowed_users=['XYZ'])
        _create_script_config_file('b2')
        _create_script_config_file('c3', allowed_users=['user1'])

        self.assert_list_config_names(self.user1, ['b2', 'c3'])

    def test_list_configs_when_none_allowed(self):
        _create_script_config_file('a1', allowed_users=['XYZ'])
        _create_script_config_file('b2', allowed_users=['ABC'])

        self.assert_list_config_names(self.user1, [])

    def test_list_configs_when_edit_mode_and_admin(self):
        _create_script_config_file('a1', allowed_users=['adm_user'])
        _create_script_config_file('c2', allowed_users=['adm_user'])

        self.assert_list_config_names(self.admin_user, ['a1', 'c2'], mode='edit')

    def test_list_configs_when_edit_mode_and_admin_without_allowance(self):
        _create_script_config_file('a1', allowed_users=['user1'])
        _create_script_config_file('c2', allowed_users=['adm_user'])

        self.assert_list_config_names(self.admin_user, ['a1', 'c2'], mode='edit')

    def test_list_configs_when_edit_mode_and_admin_not_in_admin_users(self):
        _create_script_config_file('a1', admin_users=['user1'])
        _create_script_config_file('c2', admin_users=['adm_user'])

        self.assert_list_config_names(self.admin_user, ['c2'], mode='edit')

    def test_list_configs_when_edit_mode_and_non_admin(self):
        _create_script_config_file('a1', allowed_users=['user1'])
        _create_script_config_file('c2', allowed_users=['user1'])

        self.assertRaises(AdminAccessRequiredException,
                          self.config_service.list_configs,
                          self.user1,
                          'edit')

    def test_load_config_when_user_allowed(self):
        _create_script_config_file('my_script', allowed_users=['ABC', 'user1', 'qwerty'])

        config = self.config_service.load_config_model('my_script', self.user1)
        self.assertIsNotNone(config)
        self.assertEqual('my_script', config.name)

    def test_load_config_when_user_not_allowed(self):
        _create_script_config_file('my_script', allowed_users=['ABC', 'qwerty'])

        self.assertRaises(ConfigNotAllowedException, self.config_service.load_config_model, 'my_script', self.user1)

    def assert_list_config_names(self, user, expected_names, mode=None):
        configs = self.config_service.list_configs(user, mode)
        conf_names = [config.name for config in configs]
        self.assertCountEqual(expected_names, conf_names)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['adm_user'], [], EmptyGroupProvider())
        self.user1 = User('user1', {})
        self.admin_user = User('adm_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)


class ConfigServiceCreateConfigTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user'], [], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def test_create_simple_config(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')
        self.config_service.create_config(self.admin_user, config)

        _validate_config(self, 'conf1.json', config)

    def test_non_admin_access(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')

        self.assertRaises(AdminAccessRequiredException, self.config_service.create_config,
                          User('my_user', {}), config)

    def test_blank_name(self):
        config = _prepare_script_config_object('  ', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.create_config, self.admin_user, config)

    def test_strip_name(self):
        config = _prepare_script_config_object(' conf1 ', description='My wonderful test config')

        self.config_service.create_config(self.admin_user, config)
        config['name'] = 'conf1'
        _validate_config(self, 'conf1.json', config)

    def test_blank_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        config['script_path'] = '   '

        self.assertRaises(InvalidConfigException, self.config_service.create_config,
                          self.admin_user, config)

    def test_strip_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        config['script_path'] = '  my_script.sh\t \t'

        self.config_service.create_config(self.admin_user, config)
        config['script_path'] = 'my_script.sh'
        _validate_config(self, 'Conf_X.json', config)

    def test_name_already_exists(self):
        _create_script_config_file('confX', name='confX')
        config = _prepare_script_config_object('confX', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another config with the same name already exists',
                               self.config_service.create_config, self.admin_user, config)

    def test_filename_already_exists(self):
        existing_path = _create_script_config_file('confX', name='conf-Y')
        existing_config = file_utils.read_file(existing_path)

        config = _prepare_script_config_object('confX', description='My wonderful test config')

        self.config_service.create_config(self.admin_user, config)
        _validate_config(self, 'confX_0.json', config)
        self.assertEqual(existing_config, file_utils.read_file(existing_path))

    def test_insert_sorted_values(self):
        config = _prepare_script_config_object('Conf X',
                                               requires_terminal=False,
                                               parameters=[{'name': 'param1'}],
                                               description='Some description',
                                               include='included',
                                               allowed_users=[],
                                               script_path='cd ~')

        self.config_service.create_config(self.admin_user, config)
        _validate_config(self, 'Conf_X.json', OrderedDict([('name', 'Conf X'),
                                                           ('script_path', 'cd ~'),
                                                           ('description', 'Some description'),
                                                           ('allowed_users', []),
                                                           ('include', 'included'),
                                                           ('requires_terminal', False),
                                                           ('parameters', [{'name': 'param1'}])]))

    def test_create_config_with_admin_users(self):
        config = _prepare_script_config_object('conf1',
                                               description='My wonderful test config',
                                               admin_users=['another_user'])
        self.config_service.create_config(self.admin_user, config)

        _validate_config(self, 'conf1.json', config)


class ConfigServiceUpdateConfigTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user'], [], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

        for suffix in 'XYZ':
            _create_script_config_file('conf' + suffix, name='Conf ' + suffix)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def test_update_simple_config(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        self.config_service.update_config(self.admin_user, config, 'confX.json')

        _validate_config(self, 'confX.json', config)

    def test_save_another_name(self):
        config = _prepare_script_config_object('Conf A', description='My wonderful test config')
        self.config_service.update_config(self.admin_user, config, 'confX.json')

        _validate_config(self, 'confX.json', config)
        configs_path = os.path.join(test_utils.temp_folder, 'runners')
        self.assertEqual(3, len(os.listdir(configs_path)))

    def test_non_admin_access(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')

        self.assertRaises(AdminAccessRequiredException, self.config_service.update_config,
                          User('my_user', {}), config, 'confX.json')

    def test_blank_name(self):
        config = _prepare_script_config_object('  ', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, 'confX.json')

    def test_strip_name(self):
        config = _prepare_script_config_object(' Conf X ', description='My wonderful test config')

        self.config_service.update_config(self.admin_user, config, 'confX.json')
        config['name'] = 'Conf X'
        _validate_config(self, 'confX.json', config)

    def test_blank_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        config['script_path'] = '   '

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, 'confX.json')

    def test_strip_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        config['script_path'] = '  my_script.sh\t \t'

        self.config_service.update_config(self.admin_user, config, 'confX.json')
        config['script_path'] = 'my_script.sh'
        _validate_config(self, 'confX.json', config)

    def test_name_already_exists(self):
        config = _prepare_script_config_object('Conf Y', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another script found with the same name: Conf Y',
                               self.config_service.update_config, self.admin_user, config, 'confX.json')

    def test_blank_filename(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, ' ')

    def test_filename_not_exists(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')

        self.assertRaisesRegex(InvalidFileException, 'Failed to find script path',
                               self.config_service.update_config, self.admin_user, config, 'conf A.json')

    def test_filename_already_exists(self):
        config = _prepare_script_config_object('Conf Y', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another script found with the same name: Conf Y',
                               self.config_service.update_config, self.admin_user, config, 'confX.json')

    def test_update_sorted_values(self):
        config = _prepare_script_config_object('Conf X',
                                               requires_terminal=False,
                                               parameters=[{'name': 'param1'}],
                                               description='Some description',
                                               include='included',
                                               allowed_users=[],
                                               script_path='cd ~')

        self.config_service.update_config(self.admin_user, config, 'confX.json')
        body = OrderedDict([('name', 'Conf X'),
                            ('script_path', 'cd ~'),
                            ('description', 'Some description'),
                            ('allowed_users', []),
                            ('include', 'included'),
                            ('requires_terminal', False),
                            ('parameters', [{'name': 'param1'}])])
        _validate_config(self, 'confX.json', body)

    def test_update_config_allowed_admin_user(self):
        config = _prepare_script_config_object('Conf X',
                                               description='My wonderful test config',
                                               admin_users=['admin_user'])
        self.config_service.update_config(self.admin_user, config, 'confX.json')

        new_config = _prepare_script_config_object('Conf X',
                                                   description='New desc')
        self.config_service.update_config(self.admin_user, new_config, 'confX.json')

        _validate_config(self, 'confX.json', new_config)

    def test_update_config_different_admin_user(self):
        config = _prepare_script_config_object('Conf X',
                                               description='My wonderful test config',
                                               admin_users=['another_user'])
        self.config_service.update_config(self.admin_user, config, 'confX.json')

        new_config = _prepare_script_config_object('Conf X',
                                                   description='New desc',
                                                   admin_users=['admin_user'])
        self.assertRaisesRegex(ConfigNotAllowedException, 'is not allowed to modify',
                               self.config_service.update_config, self.admin_user, new_config, 'confX.json')

        _validate_config(self, 'confX.json', config)


class ConfigServiceLoadConfigForAdminTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user'], [], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def test_load_config(self):
        _create_script_config_file('ConfX', script_path='my_script.sh', description='some desc')
        config = self.config_service.load_config('ConfX', self.admin_user)

        self.assertEqual(config, {'filename': 'ConfX.json', 'config': {'name': 'ConfX',
                                                                       'script_path': 'my_script.sh',
                                                                       'description': 'some desc'}})

    def test_load_config_when_name_different_from_filename(self):
        _create_script_config_file('ConfX', name='my conf x')
        config = self.config_service.load_config('my conf x', self.admin_user)

        self.assertEqual(config, {'filename': 'ConfX.json', 'config': {'name': 'my conf x', 'script_path': 'echo 123'}})

    def test_load_config_when_non_admin(self):
        _create_script_config_file('ConfX')
        user = User('user1', {})
        self.assertRaises(AdminAccessRequiredException, self.config_service.load_config, 'ConfX', user)

    def test_load_config_when_not_exists(self):
        _create_script_config_file('ConfX', name='my conf x')
        config = self.config_service.load_config('ConfX', self.admin_user)
        self.assertIsNone(config)

    def test_load_config_when_script_has_admin_users(self):
        _create_script_config_file('ConfX', admin_users=['admin_user'])
        config = self.config_service.load_config('ConfX', self.admin_user)
        self.assertEqual(config['filename'], 'ConfX.json')

    def test_load_config_when_script_has_different_admin_users(self):
        _create_script_config_file('ConfX', admin_users=['admin_user2'])
        self.assertRaises(ConfigNotAllowedException, self.config_service.load_config, 'ConfX', self.admin_user)


def _create_script_config_file(filename, *, name=None, **kwargs):
    conf_folder = os.path.join(test_utils.temp_folder, 'runners')
    file_path = os.path.join(conf_folder, filename + '.json')

    config = {'script_path': 'echo 123'}
    if name is not None:
        config['name'] = name

    if kwargs:
        config.update(kwargs)

    config_json = json.dumps(config)
    file_utils.write_file(file_path, config_json)
    return file_path


def _validate_config(test_case, expected_filename, expected_body):
    configs_path = os.path.join(test_utils.temp_folder, 'runners')
    path = os.path.join(configs_path, expected_filename)
    all_paths = str(os.listdir(configs_path))
    test_case.assertTrue(os.path.exists(path), 'Failed to find path ' + path + '. Existing paths: ' + all_paths)

    actual_body = custom_json.loads(file_utils.read_file(path))
    test_case.assertEqual(expected_body, actual_body)


def _prepare_script_config_object(name, **kwargs):
    config = {'name': name, 'script_path': name + '.sh'}

    if kwargs:
        config.update(kwargs)

    return config
