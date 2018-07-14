import unittest

from auth.authorization import ANY_USER
from model.server_conf import _prepare_allowed_users


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
