import json
import os
import sys
import unittest
from collections import OrderedDict
from shutil import copyfile

from parameterized import parameterized
from tornado.httputil import HTTPFile

from auth.authorization import Authorizer, EmptyGroupProvider
from auth.user import User
from config.config_service import ConfigService, ConfigNotAllowedException, AdminAccessRequiredException, \
    InvalidAccessException
from config.exceptions import InvalidConfigException
from model.model_helper import InvalidFileException
from tests import test_utils
from tests.test_utils import AnyUserAuthorizer
from utils import file_utils
from utils.audit_utils import AUTH_USERNAME
from utils.file_utils import is_executable
from utils.string_utils import is_blank


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

    def test_list_configs_when_multiple_and_subfolders(self):
        _create_script_config_file('conf_x', subfolder = 's1')
        _create_script_config_file('conf_y', subfolder = 's2')
        _create_script_config_file('ABC', subfolder = os.path.join('s1', 'inner'))

        configs = self.config_service.list_configs(self.user)
        conf_names = [config.name for config in configs]
        self.assertCountEqual(['conf_x', 'conf_y', 'ABC'], conf_names)

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
        self.assertEqual('Name with slash /', config.name)

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

        authorizer = Authorizer([], ['adm_user'], [], [], EmptyGroupProvider())
        self.user1 = User('user1', {})
        self.admin_user = User('adm_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)


def script_path(path):
    return {
        'mode': 'new_path',
        'path': path
    }


def new_code(code, filename):
    return {
        'mode': 'new_code',
        'code': code,
        'path': os.path.join(test_utils.temp_folder, 'scripts', filename)
    }


def upload_script(filename):
    return {
        'mode': 'upload_script',
        'path': os.path.join(test_utils.temp_folder, 'scripts', filename)
    }


class ConfigServiceCreateConfigTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user', 'admin_non_editor'], [], ['admin_user'], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def test_create_simple_config(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')
        self.config_service.create_config(self.admin_user, config, None)

        _validate_config(self, 'conf1.json', config)

    def test_non_admin_access(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')

        self.assertRaises(AdminAccessRequiredException, self.config_service.create_config,
                          User('my_user', {}), config, None)

    def test_blank_name(self):
        config = _prepare_script_config_object('  ', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.create_config, self.admin_user, config, None)

    def test_strip_name(self):
        config = _prepare_script_config_object(' conf1 ', description='My wonderful test config')

        self.config_service.create_config(self.admin_user, config, None)
        config['name'] = 'conf1'
        _validate_config(self, 'conf1.json', config)

    def test_blank_script_path(self):
        config = _prepare_script_config_object('Conf X',
                                               description='My wonderful test config',
                                               script=script_path('   '))

        self.assertRaises(InvalidConfigException, self.config_service.create_config,
                          self.admin_user, config, None)

    def test_strip_script_path(self):
        config = _prepare_script_config_object('Conf X',
                                               description='My wonderful test config',
                                               script=script_path('  my_script.sh\t \t'))

        self.config_service.create_config(self.admin_user, config, None)

        config['script_path'] = 'my_script.sh'
        _validate_config(self, 'Conf_X.json', config)

    def test_name_already_exists(self):
        _create_script_config_file('confX', name='confX')
        config = _prepare_script_config_object('confX', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another config with the same name already exists',
                               self.config_service.create_config, self.admin_user, config, None)

    def test_filename_already_exists(self):
        existing_path = _create_script_config_file('confX', name='conf-Y')
        existing_config = file_utils.read_file(existing_path)

        config = _prepare_script_config_object('confX', description='My wonderful test config')

        self.config_service.create_config(self.admin_user, config, None)
        _validate_config(self, 'confX_0.json', config)
        self.assertEqual(existing_config, file_utils.read_file(existing_path))

    def test_insert_sorted_values(self):
        config = _prepare_script_config_object('Conf X',
                                               requires_terminal=False,
                                               parameters=[{'name': 'param1'}],
                                               description='Some description',
                                               include='included',
                                               allowed_users=[],
                                               script=script_path('cd ~'))

        self.config_service.create_config(self.admin_user, config, None)
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
        self.config_service.create_config(self.admin_user, config, None)

        _validate_config(self, 'conf1.json', config)

    def test_new_code(self):
        config = _prepare_script_config_object('Conf X', script=new_code('abcdef', 'anything/my name.sh'))
        self.config_service.create_config(self.admin_user, config, None)

        script_path = _default_script_path('my_name')
        self.assertEqual(config['script_path'], script_path)
        _validate_config(self, 'Conf_X.json', config)
        _validate_code(self, script_path, 'abcdef')
        self.assertTrue(is_executable(script_path))

    def test_upload_code(self):
        config = _prepare_script_config_object('Conf X', script=upload_script('anything'))

        self.config_service.create_config(self.admin_user, config, HTTPFile(filename='my name.sh', body=b'xyz'))

        script_path = _default_script_path('my name')
        _validate_config(self, 'Conf_X.json', config)
        _validate_code(self, script_path, b'xyz')
        self.assertTrue(is_executable(script_path))

    @parameterized.expand([
        (None, 'filename', 'abc', 'admin_user', InvalidConfigException, 'script option is required'),
        ('new_path', ' ', 'abc', 'admin_user', InvalidConfigException, 'script.path option is required'),
        ('new_code', ' ', 'abc', 'admin_user', InvalidConfigException, 'script.path option is required'),
        ('upload_script', ' ', 'abc', 'admin_user', InvalidConfigException, 'script.path option is required'),
        ('new_code', 'Conf X.sh', 'abc', 'admin_non_editor', InvalidAccessException, 'not allowed to edit code'),
        ('upload_script', 'Conf X.sh', 'abc', 'admin_non_editor', InvalidAccessException, 'not allowed to edit code'),
        ('new_code', 'Conf X.sh', None, 'admin_user', InvalidConfigException, 'script.code should be specified'),
        ('upload_script', 'Conf X.sh', None, 'admin_user', InvalidConfigException,
         'Uploaded script should be specified'),
        ('some_mode', 'Conf X.sh', None, 'admin_user', InvalidConfigException, 'Unsupported mode'),
    ])
    def test_script_update_exceptions(self,
                                      mode,
                                      filename,
                                      content,
                                      username,
                                      expected_exception,
                                      expected_message):
        body = None
        if mode == 'new_code':
            script = {
                'mode': 'new_code',
                'code': content,
                'path': filename
            }
        elif mode == 'upload_script':
            script = {
                'mode': 'upload_script',
                'path': filename
            }
            body = HTTPFile(filename='whatever', body=content.encode('utf8')) if content else None
        elif mode == 'new_path':
            script = script_path(filename)
        elif mode is None:
            script = None
        else:
            script = {'mode': mode, 'path': filename}

        config = _prepare_script_config_object('Conf X', script=script)
        self.assertRaisesRegex(expected_exception,
                               expected_message,
                               self.config_service.create_config,
                               User(username, {}),
                               config,
                               body)


class ConfigServiceUpdateConfigTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user', 'admin_non_editor'], [], ['admin_user'], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

        for suffix in 'XYZ':
            name = 'Conf ' + suffix
            _create_script_config_file('conf' + suffix, name=name,
                                       script_path=_default_script_path(name))
            _create_script_file(name, suffix)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def test_update_simple_config(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')
        self.config_service.update_config(self.admin_user, config, 'confX.json', None)

        _validate_config(self, 'confX.json', config)

    def test_save_another_name(self):
        config = _prepare_script_config_object('Conf A', description='My wonderful test config')
        self.config_service.update_config(self.admin_user, config, 'confX.json', None)

        _validate_config(self, 'confX.json', config)
        configs_path = os.path.join(test_utils.temp_folder, 'runners')
        self.assertEqual(3, len(os.listdir(configs_path)))

    def test_non_admin_access(self):
        config = _prepare_script_config_object('conf1', description='My wonderful test config')

        self.assertRaises(AdminAccessRequiredException, self.config_service.update_config,
                          User('my_user', {}), config, 'confX.json', None)

    def test_blank_name(self):
        config = _prepare_script_config_object('  ', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, 'confX.json', None)

    def test_strip_name(self):
        config = _prepare_script_config_object(' Conf X ', description='My wonderful test config')

        self.config_service.update_config(self.admin_user, config, 'confX.json', None)
        config['name'] = 'Conf X'
        _validate_config(self, 'confX.json', config)

    def test_blank_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config', script=script_path(''))

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, 'confX.json', None)

    def test_strip_script_path(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config',
                                               script=script_path('  my_script.sh\t \t'))

        self.config_service.update_config(self.admin_user, config, 'confX.json', None)
        config['script_path'] = 'my_script.sh'
        _validate_config(self, 'confX.json', config)

    def test_name_already_exists(self):
        config = _prepare_script_config_object('Conf Y', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another script found with the same name: Conf Y',
                               self.config_service.update_config, self.admin_user, config, 'confX.json', None)

    def test_blank_filename(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')

        self.assertRaises(InvalidConfigException, self.config_service.update_config,
                          self.admin_user, config, ' ', None)

    def test_filename_not_exists(self):
        config = _prepare_script_config_object('Conf X', description='My wonderful test config')

        self.assertRaisesRegex(InvalidFileException, 'Failed to find script path',
                               self.config_service.update_config, self.admin_user, config, 'conf A.json', None)

    def test_filename_already_exists(self):
        config = _prepare_script_config_object('Conf Y', description='My wonderful test config')

        self.assertRaisesRegex(InvalidConfigException, 'Another script found with the same name: Conf Y',
                               self.config_service.update_config, self.admin_user, config, 'confX.json', None)

    def test_update_sorted_values(self):
        config = _prepare_script_config_object('Conf X',
                                               requires_terminal=False,
                                               parameters=[{'name': 'param1'}],
                                               description='Some description',
                                               include='included',
                                               allowed_users=[],
                                               script=script_path('cd ~'))

        self.config_service.update_config(self.admin_user, config, 'confX.json', None)
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
        self.config_service.update_config(self.admin_user, config, 'confX.json', None)

        new_config = _prepare_script_config_object('Conf X',
                                                   description='New desc')
        self.config_service.update_config(self.admin_user, new_config, 'confX.json', None)

        _validate_config(self, 'confX.json', new_config)

    @parameterized.expand([('Conf X',), ('Conf X111',)])
    def test_update_config_different_admin_user(self, new_name):
        config = _prepare_script_config_object('Conf X',
                                               description='My wonderful test config',
                                               admin_users=['another_user'])
        self.config_service.update_config(self.admin_user, config, 'confX.json', None)

        new_config = _prepare_script_config_object(new_name,
                                                   description='New desc',
                                                   admin_users=['admin_user'])
        self.assertRaisesRegex(ConfigNotAllowedException, 'is not allowed to modify',
                               self.config_service.update_config, self.admin_user, new_config, 'confX.json', None)

        _validate_config(self, 'confX.json', config)

    def test_update_config_new_code(self):
        config = _prepare_script_config_object('Conf X', script=new_code('abcdef', 'Conf X.sh'))
        self.config_service.update_config(self.admin_user, config, 'confX.json', None)

        _validate_config(self, 'confX.json', config)
        _validate_code(self, _default_script_path('Conf X'), 'abcdef')
        self.assertTrue(is_executable(_default_script_path('Conf X')))

    def test_update_config_upload_code(self):
        config = _prepare_script_config_object('Conf X', script=upload_script('Conf X.sh'))
        body = bytes.fromhex('4D5A')
        self.config_service.update_config(self.admin_user, config, 'confX.json',
                                          HTTPFile(filename='whatever', body=body))

        _validate_config(self, 'confX.json', config)
        _validate_code(self, _default_script_path('Conf X'), body)
        self.assertTrue(is_executable(_default_script_path('Conf X')))

    @parameterized.expand([
        (None, 'filename', 'abc', 'admin_user', InvalidConfigException, 'script option is required'),
        ('new_path', ' ', 'abc', 'admin_user', InvalidConfigException, 'script.path option is required'),
        ('new_code', 'Conf X.sh', 'abc', 'admin_non_editor', InvalidAccessException, 'not allowed to edit code'),
        ('upload_script', 'Conf X.sh', 'abc', 'admin_non_editor', InvalidAccessException, 'not allowed to edit code'),
        ('new_code', 'another.sh', 'abc', 'admin_user', InvalidConfigException, 'script.path override is not allowed'),
        ('upload_script', 'another.sh', 'abc', 'admin_user', InvalidConfigException,
         'script.path override is not allowed'),
        ('new_code', 'Conf X.sh', None, 'admin_user', InvalidConfigException, 'script.code should be specified'),
        ('upload_script', 'Conf X.sh', None, 'admin_user', InvalidConfigException,
         'Uploaded script should be specified'),
        ('some_mode', 'Conf X.sh', None, 'admin_user', InvalidConfigException, 'Unsupported mode'),
    ])
    def test_update_config_script_update_exceptions(self, mode,
                                                    filename,
                                                    content,
                                                    username,
                                                    expected_exception,
                                                    expected_message):
        body = None
        if mode == 'new_code':
            script = new_code(content, filename)
        elif mode == 'upload_script':
            script = upload_script(filename)
            body = HTTPFile(filename='whatever', body=content.encode('utf8')) if content else None
        elif mode == 'new_path':
            script = script_path(filename)
        elif mode is None:
            script = None
        else:
            script = {'mode': mode, 'path': filename}

        config = _prepare_script_config_object('Conf X', script=script)
        self.assertRaisesRegex(expected_exception,
                               expected_message,
                               self.config_service.update_config,
                               User(username, {}),
                               config,
                               'confX.json',
                               body)

    @parameterized.expand([
        ('new_code', '  ', InvalidFileException, 'Script path is not specified'),
        ('upload_script', '  ', InvalidFileException, 'Script path is not specified'),
        ('new_code', 'tests_temp/python', InvalidConfigException, 'Cannot edit binary file'),
        ('upload_script', 'tests_temp/python', None, None),
        ('new_code', 'tests_temp/python tests_temp/python', InvalidFileException,
         'Cannot choose which binary file to edit'),
        ('upload_script', 'tests_temp/python tests_temp/python', InvalidFileException,
         'Cannot choose which binary file to edit'),
        ('new_code', 'tests_temp/something.sh', InvalidConfigException, 'Script path does not exist'),
        ('upload_script', 'tests_temp/something.sh', None, None),
        ('upload_script', 'tests_temp/some  thing.sh', InvalidFileException, 'Failed to find script path'),
        ('upload_script', '"tests_temp/some  thing.sh"', None, None),
    ])
    def test_update_config_script_update_when_code_loading_problems(
            self,
            mode,
            original_script_path,
            expected_exception,
            expected_message):

        copyfile(sys.executable, os.path.join(test_utils.temp_folder, 'python'))

        body = None
        if mode == 'new_code':
            script = {
                'mode': 'new_code',
                'code': 'abcdef',
                'path': original_script_path if not is_blank(original_script_path) else 'anything'
            }
        elif mode == 'upload_script':
            script = {
                'mode': 'upload_script',
                'path': original_script_path if not is_blank(original_script_path) else 'anything'
            }
            body = HTTPFile(filename='whatever', body=b'xyz')
        else:
            script = None

        _create_script_config_file('ConfA', name='ConfA', script_path=original_script_path)

        config = _prepare_script_config_object('ConfA', script=script)
        if expected_exception is not None:
            self.assertRaisesRegex(expected_exception,
                                   expected_message,
                                   self.config_service.update_config,
                                   self.admin_user,
                                   config,
                                   'ConfA.json',
                                   body)
        else:
            self.config_service.update_config(
                self.admin_user,
                config,
                'ConfA.json',
                body)


class ConfigServiceLoadConfigForAdminTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user'], [], [], EmptyGroupProvider())
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


class ConfigServiceLoadCodeTest(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

        authorizer = Authorizer([], ['admin_user', 'admin_non_editor'], [], ['admin_user'], EmptyGroupProvider())
        self.admin_user = User('admin_user', {})
        self.config_service = ConfigService(authorizer, test_utils.temp_folder)

        for pair in [('script.py', b'123'),
                     ('another.py', b'xyz'),
                     ('binary 1.bin', bytes.fromhex('300000004000000a')),
                     ('my_python', bytes.fromhex('7F454C46'))]:
            path = os.path.join(test_utils.temp_folder, pair[0])
            file_utils.write_file(path, pair[1], byte_content=True)

    @parameterized.expand([
        ('tests_temp/script.py',),
        ('tests_temp/script.py tests_temp/another.py',),
        ('python tests_temp/script.py',),
        ('/usr/bin/python3 -U tests_temp/script.py',),
        ('tests_temp/my_python tests_temp/script.py',),
        ('some/unknown/file tests_temp/script.py',)
    ])
    def test_load_without_errors(self, command):
        _create_script_config_file('ConfX', script_path=command)

        self.assert_script_code('tests_temp/script.py', '123', None)

    @parameterized.expand([
        ('tests_temp/my_python', 'tests_temp/my_python', 'Cannot edit binary file'),
        ('tests_temp/binary 1.bin', 'tests_temp/binary 1.bin', 'Cannot edit binary file'),
        ('tests_temp/unknown.py', 'tests_temp/unknown.py', 'Script path does not exist'),
        ('"tests_temp/unknown with spaces.bin"', 'tests_temp/unknown with spaces.bin', 'Script path does not exist'),
    ])
    def test_load_with_warnings(self, command, expected_path, expected_error):
        _create_script_config_file('ConfX', script_path=command)

        self.assert_script_code(expected_path, None, expected_error)

    @parameterized.expand([
        ('  ', 'Script path is not specified'),
        ('tests_temp/my_python "tests_temp/binary 1.bin"', 'Cannot choose which binary file to edit'),
        ('tests_temp/unknown with spaces.bin', 'Failed to find script path in command'),
    ])
    def test_load_with_errors(self, command, expected_message):
        _create_script_config_file('ConfX', script_path=command)

        self.assertRaisesRegex(InvalidFileException,
                               expected_message,
                               self.config_service.load_script_code,
                               'ConfX',
                               self.admin_user)

    def test_load_without_permissions(self):
        _create_script_config_file('ConfX', script_path='tests_temp/script.py')

        self.assertRaisesRegex(InvalidAccessException,
                               'Code edit is not allowed for this user',
                               self.config_service.load_script_code,
                               'ConfX',
                               User('admin_non_editor', {}))

    def test_load_without_config(self):
        _create_script_config_file('ConfX', script_path='tests_temp/script.py')

        code = self.config_service.load_script_code('Conf123', self.admin_user)
        self.assertIsNone(code)

    def assert_script_code(self, script_path, code, error):
        script_code = self.config_service.load_script_code('ConfX', self.admin_user)
        if 'code_edit_error' not in script_code:
            script_code['code_edit_error'] = None

        if not os.path.isabs(script_code['file_path']):
            script_code['file_path'] = file_utils.normalize_path(script_code['file_path'])

        self.assertEqual({
            'code': code,
            'file_path': file_utils.normalize_path(script_path),
            'code_edit_error': error
        }, script_code)

    def tearDown(self) -> None:
        super().tearDown()
        test_utils.cleanup()


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


def _create_script_file(name, code):
    file_path = _default_script_path(name)

    file_utils.write_file(file_path, code)
    return file_path


def _validate_config(test_case, expected_filename, expected_body):
    configs_path = os.path.join(test_utils.temp_folder, 'runners')
    path = os.path.join(configs_path, expected_filename)
    all_paths = str(os.listdir(configs_path))
    test_case.assertTrue(os.path.exists(path), 'Failed to find path ' + path + '. Existing paths: ' + all_paths)

    actual_body = json.loads(file_utils.read_file(path))
    test_case.assertEqual(expected_body, actual_body)


def _validate_code(test_case, script_path, expected_code):
    path = script_path

    actual_code = file_utils.read_file(path, byte_content=True)
    if isinstance(expected_code, str):
        expected_code = expected_code.encode('utf8')

    test_case.assertEqual(expected_code, actual_code)


def _default_script_path(name):
    return os.path.join(test_utils.temp_folder, 'scripts', name + '.sh')


def _prepare_script_config_object(name, **kwargs):
    config = {'name': name, 'script': {'path': name + '.sh'}}

    if kwargs:
        config.update(kwargs)

    return config
