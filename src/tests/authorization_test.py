import unittest
from collections import defaultdict

from auth.authorization import Authorizer, ANY_USER, PreconfiguredGroupProvider, create_group_provider


class TestIsAllowed(unittest.TestCase):
    def test_allowed_from_single_user(self):
        self.assertTrue(self.authorizer.is_allowed('user1', ['user1']))

    def test_not_allowed_from_single_user(self):
        self.assertFalse(self.authorizer.is_allowed('user1', ['user2']))

    def test_allowed_from_multiple_users(self):
        self.assertTrue(self.authorizer.is_allowed('userX', ['user1', 'user2', 'userX', 'user3']))

    def test_not_allowed_from_multiple_users(self):
        self.assertFalse(self.authorizer.is_allowed('userX', ['user1', 'user2', 'user3']))

    def test_allowed_from_single_group(self):
        self.user_groups['user1'] = ['group1']
        self.assertTrue(self.authorizer.is_allowed('user1', ['@group1']))

    def test_not_allowed_from_single_group_invalid_name_in_provider(self):
        self.user_groups['user1'] = ['@group1']
        self.assertFalse(self.authorizer.is_allowed('user1', ['@group1']))

    def test_not_allowed_from_single_group_invalid_name_in_list(self):
        self.user_groups['user1'] = ['group1']
        self.assertFalse(self.authorizer.is_allowed('user1', ['group1']))

    def test_allowed_from_multiple_groups_when_one_match(self):
        self.user_groups['user1'] = ['group1', 'groupX']
        self.assertTrue(self.authorizer.is_allowed('user1', ['@group1', '@group2', '@group3']))

    def test_allowed_from_multiple_groups_when_multiple_match(self):
        self.user_groups['user1'] = ['group3', 'group2']
        self.assertTrue(self.authorizer.is_allowed('user1', ['@group1', '@group2', '@group3']))

    def test_not_allowed_from_multiple_groups(self):
        self.user_groups['user1'] = ['groupX', 'groupY']
        self.assertFalse(self.authorizer.is_allowed('user1', ['@group1', '@group2', '@group3']))

    def test_allowed_from_any_user_list(self):
        self.assertTrue(self.authorizer.is_allowed('user1', [ANY_USER]))

    def test_allowed_from_any_user_single(self):
        self.assertTrue(self.authorizer.is_allowed('user1', ANY_USER))

    def test_not_allowed_from_empty(self):
        self.assertFalse(self.authorizer.is_allowed('user1', []))

    def get_groups(self, user):
        return self.user_groups[user]

    def setUp(self):
        super().setUp()

        self.user_groups = defaultdict(list)

        self.authorizer = Authorizer([], [], self)


class TestPreconfiguredGroupProvider(unittest.TestCase):
    def test_single_user_in_single_group(self):
        provider = PreconfiguredGroupProvider({'group1': ['user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])

    def test_two_users_in_different_groups(self):
        provider = PreconfiguredGroupProvider(
            {'group1': ['user1'],
             'group2': ['user2']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), ['group2'])

    def test_user_without_groups(self):
        provider = PreconfiguredGroupProvider({'group1': ['user1']})
        self.assertCountEqual(provider.get_groups('user2'), [])

    def test_user_in_multiple_groups(self):
        provider = PreconfiguredGroupProvider({'group1': ['user1'], 'group2': ['user1'], 'group3': ['user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2', 'group3'])

    def test_empty_group(self):
        provider = PreconfiguredGroupProvider({'group1': []})
        self.assertCountEqual(provider.get_groups('user1'), [])

    def test_empty_groups_config(self):
        provider = PreconfiguredGroupProvider({})
        self.assertCountEqual(provider.get_groups('user1'), [])

    def test_user_in_recursive_group_when_2_levels(self):
        provider = PreconfiguredGroupProvider({'group1': ['user1'], 'group2': ['@group1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2'])

    def test_user_in_recursive_group_when_3_levels(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2'], 'group2': ['@group3'], 'group3': ['user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2', 'group3'])

    def test_user_in_recursive_groups_when_cyclic(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2'], 'group2': ['@group1', 'user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2'])

    def test_2_users_in_recursive_groups_when_cyclic(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2', 'user2'], 'group2': ['@group1', 'user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2'])
        self.assertCountEqual(provider.get_groups('user2'), ['group1', 'group2'])


class TestCreateGroupProvider(unittest.TestCase):
    def test_create_from_groups_only(self):
        provider = create_group_provider({'group1': ['user1']}, None, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), [])

    def test_create_from_all_none(self):
        provider = create_group_provider(None, None, None)
        self.assertCountEqual(provider.get_groups('user1'), [])

    def test_create_from_admin_users_only(self):
        provider = create_group_provider(None, None, ['user1'])
        self.assertCountEqual(provider.get_groups('user1'), ['admin_users'])
        self.assertCountEqual(provider.get_groups('user2'), [])

    def test_create_from_group_and_admin_users(self):
        provider = create_group_provider({'group1': ['user1', 'user2']}, None, ['user1'])
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'admin_users'])
        self.assertCountEqual(provider.get_groups('user2'), ['group1'])

    def test_create_from_group_and_admin_users_when_admin_group_exists(self):
        provider = create_group_provider({'group1': ['user1'], 'admin_users': ['user2']}, None, ['user1'])
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), ['admin_users'])

    def test_create_from_groups_and_empty_authenticator(self):
        auth = self._create_authenticator({})
        provider = create_group_provider({'group1': ['user1']}, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), [])

    def test_create_from_groups_and_authenticator_when_same_group(self):
        auth = self._create_authenticator({'user1': ['group1']})
        provider = create_group_provider({'group1': ['user1']}, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])

    def test_create_from_groups_and_authenticator_when_different_groups(self):
        auth = self._create_authenticator({'user1': ['group2']})
        provider = create_group_provider({'group1': ['user1']}, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2'])

    def test_create_from_groups_and_authenticator_when_different_users(self):
        auth = self._create_authenticator({'user2': ['group2']})
        provider = create_group_provider({'group1': ['user1']}, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), ['group2'])

    def test_create_from_authenticator_only(self):
        auth = self._create_authenticator({'user1': ['group1']})
        provider = create_group_provider(None, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])

    def _create_authenticator(self, user_groups):
        class GroupTestAuthenticator:
            def get_groups(self, user):
                return user_groups.get(user)

        return GroupTestAuthenticator()
