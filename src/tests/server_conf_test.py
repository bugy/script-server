import json
import os
import unittest

from auth.authorization import ANY_USER
from model import server_conf
from model.server_conf import _prepare_allowed_users
from tests import test_utils
from utils import file_utils


class TestPrepareAllowedUsers(unittest.TestCase):
    def test_keep_allowed_users_without_admins_and_groups(self):
        allowed_users = _prepare_allowed_users(['user1', 'user2'], None, None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_coerce_none_users_to_any(self):
        allowed_users = _prepare_allowed_users(None, None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users('*', None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_list_with_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users(['user1', '*', 'user2'], None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_list_with_untrimmed_asterisk_to_any(self):
        allowed_users = _prepare_allowed_users(['user1', '\t*  ', 'user2'], None, None)
        self.assertCountEqual([ANY_USER], allowed_users)

    def test_coerce_untrimmed_values(self):
        allowed_users = _prepare_allowed_users([' user1 ', ' ', '\tuser2\t'], None, None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_admin_users(self):
        allowed_users = _prepare_allowed_users(['user1'], ['user2'], None)
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_admin_users_with_same(self):
        allowed_users = _prepare_allowed_users(['user1', 'user2'], ['user2', 'user3'], None)
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_users_from_1_group(self):
        allowed_users = _prepare_allowed_users(['user1'], None, {'group1': ['user2']})
        self.assertCountEqual(['user1', 'user2'], allowed_users)

    def test_add_group_users_from_2_groups(self):
        allowed_users = _prepare_allowed_users(['user1'], None, {'group1': ['user2'], 'group2': ['user3']})
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_users_from_2_groups_when_same(self):
        allowed_users = _prepare_allowed_users(
            ['user1', 'user2'], None,
            {'group1': ['user2', 'user3'], 'group2': ['user4', 'user3']})
        self.assertCountEqual(['user1', 'user2', 'user3', 'user4'], allowed_users)

    def test_add_group_and_admin_users(self):
        allowed_users = _prepare_allowed_users(
            ['user1'], ['user2'], {'group1': ['user3']})
        self.assertCountEqual(['user1', 'user2', 'user3'], allowed_users)

    def test_add_group_and_admin_users_when_same(self):
        allowed_users = _prepare_allowed_users(
            ['user1', 'user2', 'user3'],
            ['user2', 'userX'],
            {'group1': ['userY', 'user3']})
        self.assertCountEqual(['user1', 'user2', 'user3', 'userX', 'userY'], allowed_users)


class TestAdminUsersInit(unittest.TestCase):
    def test_single_list(self):
        config = _from_json({'access': {'admin_users': ['userX']}})
        self.assertEqual(['userX'], config.admin_users)

    def test_single_string(self):
        config = _from_json({'access': {'admin_users': 'abc'}})
        self.assertEqual(['abc'], config.admin_users)

    def test_missing_when_no_auth(self):
        config = _from_json({})
        self.assertEqual(['127.0.0.1', '::1'], config.admin_users)

    def test_missing_when_auth_enabled(self):
        config = _from_json({'auth': {'type': 'ldap', 'url': 'localhost'}})
        self.assertEqual([], config.admin_users)

    def test_list_with_multiple_values(self):
        config = _from_json({'access': {'admin_users': ['user1', 'user2', 'user3']}})
        self.assertCountEqual(['user1', 'user2', 'user3'], config.admin_users)

    def test_list_with_any_user(self):
        config = _from_json({'access': {'admin_users': ['user1', '*', 'user3']}})
        self.assertEqual([ANY_USER], config.admin_users)

    def test_list_any_user_single_string(self):
        config = _from_json({'access': {'admin_users': '*'}})
        self.assertCountEqual([ANY_USER], config.admin_users)

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestMaxRequestSize(unittest.TestCase):
    def test_int_value(self):
        config = _from_json({'max_request_size': 5})
        self.assertEqual(5, config.max_request_size_mb)

    def test_string_value(self):
        config = _from_json({'max_request_size': '123'})
        self.assertEqual(123, config.max_request_size_mb)

    def test_default_value(self):
        config = _from_json({})
        self.assertEqual(10, config.max_request_size_mb)


def _from_json(content):
    json_obj = json.dumps(content)
    conf_path = os.path.join(test_utils.temp_folder, 'conf.json')
    file_utils.write_file(conf_path, json_obj)
    return server_conf.from_json(conf_path, test_utils.temp_folder)
