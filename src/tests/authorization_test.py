import unittest
from collections import defaultdict

from auth.authorization import Authorizer, ANY_USER, PreconfiguredGroupProvider, create_group_provider, \
    EmptyGroupProvider


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


class TestIsAllowedInApp(unittest.TestCase):
    def test_single_user_allowed(self):
        self.assertAllowed('user1', ['user1'], True)

    def test_multiple_users_allowed(self):
        self.assertAllowed('user2', ['user1', 'user2', 'user3'], True)

    def test_multiple_users_not_allowed(self):
        self.assertAllowed('user4', ['user1', 'user2', 'user3'], False)

    def test_any_user_allowed(self):
        self.assertAllowed('user5', [ANY_USER], True)

    def test_any_user_allowed_when_mixed(self):
        self.assertAllowed('user5', ['user1', ANY_USER, 'user2'], True)

    def test_allowed_user_when_in_group(self):
        self.assertAllowed('user5', ['user1', 'user2', '@my_group'], True, groups={'my_group': ['user5']})

    def test_not_allowed_user_when_not_in_group(self):
        self.assertAllowed('user5', ['user1', 'user2', '@my_group'], False, groups={'my_group': ['user3']})

    def assertAllowed(self, user, allowed_users, expected_allowed, groups=None):
        group_provider = PreconfiguredGroupProvider(groups) if groups else EmptyGroupProvider()
        authorizer = Authorizer(allowed_users, [], group_provider)

        allowed = authorizer.is_allowed_in_app(user)
        if allowed != expected_allowed:
            self.fail('Expected ' + user + ' to be allowed=' + str(expected_allowed)
                      + ' for ' + str(allowed_users) + ' but was ' + str(allowed))


class TestIsAdmin(unittest.TestCase):
    def test_single_admin_allowed(self):
        self.assertAdmin('admin1', ['admin1'], True)

    def test_multiple_admins_allowed(self):
        self.assertAdmin('admin2', ['admin1', 'admin2', 'admin3'], True)

    def test_multiple_admins_not_allowed(self):
        self.assertAdmin('user1', ['admin1', 'admin2', 'admin3'], False)

    def test_any_user_is_admin(self):
        self.assertAdmin('admin5', [ANY_USER], True)

    def test_any_admin_when_mixed(self):
        self.assertAdmin('admin5', ['admin1', ANY_USER, 'admin2'], True)

    def test_is_admin_when_in_group(self):
        self.assertAdmin('admin5', ['admin1', 'admin2', '@my_group'], True, groups={'my_group': ['admin5']})

    def test_not_admin_admin_when_not_in_group(self):
        self.assertAdmin('admin5', ['admin1', 'admin2', '@my_group'], False, groups={'my_group': ['admin3']})

    def assertAdmin(self, user, admin_users, expected_allowed, groups=None):
        group_provider = PreconfiguredGroupProvider(groups) if groups else EmptyGroupProvider()
        authorizer = Authorizer([], admin_users, group_provider)

        allowed = authorizer.is_admin(user)
        if allowed != expected_allowed:
            self.fail('Expected ' + user + ' to be admin=' + str(expected_allowed)
                      + ' for ' + str(admin_users) + ' but was ' + str(allowed))


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

    def test_create_from_group_and_admin_users_when_admin_group_has_unknown_group(self):
        provider = create_group_provider({'group1': ['user1']}, None, ['user2', '@some_group'])
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), ['admin_users'])

    def test_create_from_group_including_admin_users_when_admin_group_has_unknown_group(self):
        provider = create_group_provider({'group1': ['user1', '@admin_users']}, None, ['user2', '@some_group'])
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])
        self.assertCountEqual(provider.get_groups('user2'), ['admin_users', 'group1'])

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
