import unittest
from collections import defaultdict

from auth.authorization import Authorizer, ANY_USER, PreconfiguredGroupProvider, create_group_provider, \
    EmptyGroupProvider, CombinedGroupProvider


class TestIsAllowed(unittest.TestCase):
    def test_allowed_from_single_user(self):
        self.assertTrue(self.authorizer.is_allowed('user1', ['user1']))

    def test_allowed_from_single_user_ignore_case(self):
        self.assertTrue(self.authorizer.is_allowed('USer1', ['usER1']))

    def test_not_allowed_from_single_user(self):
        self.assertFalse(self.authorizer.is_allowed('user1', ['user2']))

    def test_allowed_from_multiple_users(self):
        self.assertTrue(self.authorizer.is_allowed('userX', ['user1', 'user2', 'userX', 'user3']))

    def test_not_allowed_from_multiple_users(self):
        self.assertFalse(self.authorizer.is_allowed('userX', ['user1', 'user2', 'user3']))

    def test_allowed_from_single_group(self):
        self.user_groups['user1'] = ['group1']
        self.assertTrue(self.authorizer.is_allowed('user1', ['@group1']))

    def test_allowed_from_single_group_ignore_case(self):
        self.user_groups['user1'] = ['Group1']
        self.assertTrue(self.authorizer.is_allowed('user1', ['@groUP1']))

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

    def get_groups(self, user, known_groups=None):
        return self.user_groups[user]

    def setUp(self):
        super().setUp()

        self.user_groups = defaultdict(list)

        self.authorizer = Authorizer([], [], [], [], self)


class TestIsAllowedInApp(unittest.TestCase):
    def test_single_user_allowed(self):
        self.assertAllowed('user1', ['user1'], True)

    def test_single_user_allowed_ignore_case(self):
        self.assertAllowed('User1', ['uSEr1'], True)

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
        authorizer = Authorizer(allowed_users, [], [], [], group_provider)

        allowed = authorizer.is_allowed_in_app(user)
        if allowed != expected_allowed:
            self.fail('Expected ' + user + ' to be allowed=' + str(expected_allowed)
                      + ' for ' + str(allowed_users) + ' but was ' + str(allowed))


class TestIsAdmin(unittest.TestCase):
    def test_single_admin_allowed(self):
        self.assertAdmin('admin1', ['admin1'], True)

    def test_single_admin_allowed_ignore_case(self):
        self.assertAdmin('adMin1', ['AdmiN1'], True)

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
        authorizer = Authorizer([], admin_users, [], [], group_provider)

        allowed = authorizer.is_admin(user)
        if allowed != expected_allowed:
            self.fail('Expected ' + user + ' to be admin=' + str(expected_allowed)
                      + ' for ' + str(admin_users) + ' but was ' + str(allowed))


class TestHistoryAccess(unittest.TestCase):
    def test_user_in_the_list(self):
        self.assert_has_access('user1', [], ['user1'], True)

    def test_user_in_the_list_ignore_case(self):
        self.assert_has_access('useR1', [], ['UsEr1'], True)

    def test_any_user_allowed(self):
        self.assert_has_access('user2', [], [ANY_USER], True)

    def test_user_not_in_the_list(self):
        self.assert_has_access('user1', [], ['user2', 'user3', 'user4'], False)

    def test_user_not_in_the_list_when_empty(self):
        self.assert_has_access('user1', [], [], False)

    def test_user_is_admin(self):
        self.assert_has_access('admin1', ['admin1'], [], True)

    def test_has_access_when_in_group(self):
        self.assert_has_access('user1', [], ['@group1'], True, groups={'group1': ['user1']})

    def test_has_access_when_in_group_without_access(self):
        self.assert_has_access('user1', [], ['@group2'], False, groups={'group1': ['user1']})

    def assert_has_access(self, user, admin_users, history_access_users, expected_allowed, groups=None):
        group_provider = PreconfiguredGroupProvider(groups) if groups else EmptyGroupProvider()
        authorizer = Authorizer([], admin_users, history_access_users, [], group_provider)

        has_access = authorizer.has_full_history_access(user)
        if has_access != expected_allowed:
            self.fail('Expected ' + user + ' to has_access=' + str(expected_allowed)
                      + ' for ' + str(history_access_users) + ' but was ' + str(has_access))


class TestPreconfiguredGroupProvider(unittest.TestCase):
    def test_single_user_in_single_group(self):
        provider = PreconfiguredGroupProvider({'group1': ['user1']})
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])

    def test_single_user_in_single_group_ignore_case(self):
        provider = PreconfiguredGroupProvider({'group1': ['USER1']})
        self.assertCountEqual(provider.get_groups('User1'), ['group1'])

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

    def test_known_group_when_exists(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2', 'user2']})
        self.assertCountEqual(provider.get_groups('user1', known_groups=['group2']), ['group1'])

    def test_known_group_when_exists_and_multiple_and_mixed(self):
        provider = PreconfiguredGroupProvider(
            {'group1': ['@lazy1', 'user2'],
             'group2': ['@lazy2', 'user3'],
             'group3': ['@lazy3', 'user1'],
             'group4': ['@lazy4', 'user4']})
        actual_groups = provider.get_groups('user1', known_groups=['lazy2', 'lazy4'])
        self.assertCountEqual(actual_groups, ['group2', 'group3', 'group4'])

    def test_known_group_when_duplicated(self):
        provider = PreconfiguredGroupProvider(
            {'group1': ['@lazy1', 'user1'],
             'group2': ['@lazy21', '@lazy22', 'user2'],
             'group3': ['@lazy3', 'user3']})
        actual_groups = provider.get_groups('user1', known_groups=['lazy1', 'lazy21', 'lazy22'])
        self.assertCountEqual(actual_groups, ['group1', 'group2'])

    def test_known_group_when_multiple_parents(self):
        provider = PreconfiguredGroupProvider(
            {'group1': ['@lazy1', 'user1'],
             'group2': ['@lazy1', '@lazy2', 'user2'],
             'group3': ['@lazy3', 'user3']})
        actual_groups = provider.get_groups('userX', known_groups=['lazy1'])
        self.assertCountEqual(actual_groups, ['group1', 'group2'])

    def test_known_group_when_not_exists(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2', 'user2']})
        self.assertCountEqual(provider.get_groups('user1', known_groups=['group3']), [])

    def test_known_group_when_username_starts_with_at(self):
        provider = PreconfiguredGroupProvider({'group1': ['@group2', 'user2']})
        self.assertCountEqual(provider.get_groups('@group2'), [])


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

    def test_known_groups_when_create_from_authenticator_and_preconfigured(self):
        auth = self._create_authenticator({'user1': ['group1']})
        provider = create_group_provider({'group2': ['@group1']}, auth, None)
        self.assertCountEqual(provider.get_groups('user1'), ['group1', 'group2'])

    def _create_authenticator(self, user_groups):
        class GroupTestAuthenticator:
            def get_groups(self, user, known_groups=None):
                return user_groups.get(user)

        return GroupTestAuthenticator()


class TestCombinedGroupProvider(unittest.TestCase):
    def test_single_provider(self):
        provider = CombinedGroupProvider(PreconfiguredGroupProvider({'group1': ['user1', 'user2']}))
        self.assertCountEqual(provider.get_groups('user1'), ['group1'])

    def test_multiple_providers(self):
        provider = CombinedGroupProvider(
            PreconfiguredGroupProvider({'group1': ['user1', 'user2']}),
            PreconfiguredGroupProvider({'group2': ['user3', 'user4']}),
            PreconfiguredGroupProvider({'group3': ['user2', 'user5']}))
        self.assertCountEqual(provider.get_groups('user2'), ['group1', 'group3'])

    def test_multiple_providers_when_same_groups(self):
        provider = CombinedGroupProvider(
            PreconfiguredGroupProvider({'group1': ['user1', 'user2']}),
            PreconfiguredGroupProvider({'group2': ['user3', 'user4']}),
            PreconfiguredGroupProvider({'group1': ['user2', 'user5']}))
        self.assertCountEqual(provider.get_groups('user2'), ['group1'])

    def test_known_groups_when_single_provider(self):
        provider = CombinedGroupProvider(
            PreconfiguredGroupProvider({'group1': ['user1', '@lazy1']}))
        self.assertCountEqual(provider.get_groups('user2', ['lazy1']), ['group1'])

    def test_known_groups_when_multiple_provider(self):
        provider = CombinedGroupProvider(
            PreconfiguredGroupProvider({'group1': ['@lazy1', 'user1']}),
            PreconfiguredGroupProvider({'group2': ['userX', 'user2']}),
            PreconfiguredGroupProvider({'group3': ['user3']}),
            PreconfiguredGroupProvider({'group4': ['@lazy4', 'user4']}))
        self.assertCountEqual(provider.get_groups('userX', ['lazy1', 'lazy4']), ['group1', 'group2', 'group4'])

    def test_known_groups_when_multiple_dependant_providers(self):
        provider = CombinedGroupProvider(
            PreconfiguredGroupProvider({'group1': ['@lazy1', 'user1']}),
            PreconfiguredGroupProvider({'group2': ['@group1', 'user2']}),
            PreconfiguredGroupProvider({'group3': ['userX']}),
            PreconfiguredGroupProvider({'group4': ['user4']}),
            PreconfiguredGroupProvider({'group5': ['@group3', '@group4']}))
        self.assertCountEqual(provider.get_groups('userX', ['lazy1']), ['group1', 'group2', 'group3', 'group5'])
