from collections import defaultdict

ANY_USER = '__ANY_USER'
ADMIN_GROUP = 'admin_users'
GROUP_PREFIX = '@'


class Authorizer:
    def __init__(self, app_allowed_users, admin_users, groups_provider):
        self._app_allowed_users = app_allowed_users
        self._admin_users = admin_users

        self._groups_provider = groups_provider

    def is_allowed_in_app(self, user_id):
        return self.is_allowed(user_id, self._app_allowed_users)

    def is_admin(self, user_id):
        return self.is_allowed(user_id, self._admin_users)

    def is_allowed(self, user_id, allowed_users):
        if not allowed_users:
            return False

        if (allowed_users == ANY_USER) or (ANY_USER in allowed_users):
            return True

        if user_id in allowed_users:
            return True

        user_groups = self._groups_provider.get_groups(user_id)
        if not user_groups:
            return False

        for group in user_groups:
            if (GROUP_PREFIX + group) in allowed_users:
                return True

        return False


class EmptyGroupProvider:

    def get_groups(self, user):
        return []


def _flatten_groups(groups):
    result = {}

    for group in groups.keys():
        group_users = set()
        visited_groups = set()

        queue = [group]

        while queue:
            current_group = queue.pop()
            if current_group in visited_groups:
                continue
            visited_groups.add(current_group)

            if current_group in result:
                group_users.update(result[current_group])
                continue

            current_group_members = groups[current_group]
            for member in current_group_members:
                if member.startswith(GROUP_PREFIX):
                    queue.append(member[1:])
                else:
                    group_users.add(member)

        result[group] = group_users

    return result


class PreconfiguredGroupProvider:

    def __init__(self, groups) -> None:
        self._user_groups = defaultdict(list)

        flat_groups = _flatten_groups(groups)
        for group, users in flat_groups.items():
            for user in users:
                self._user_groups[user].append(group)

    def get_groups(self, user):
        return self._user_groups[user]


class CombinedGroupProvider:

    def __init__(self, *other_providers) -> None:
        self._other_providers = list(other_providers)

    def get_groups(self, user):
        groups = set()
        for provider in self._other_providers:
            provider_groups = provider.get_groups(user)
            if provider_groups:
                groups.update(provider_groups)

        return groups


def create_group_provider(user_groups, authenticator, admin_users):
    if admin_users:
        admin_users = _exclude_unknown_groups_from_admin_users(admin_users, user_groups)
        if user_groups is None:
            user_groups = {ADMIN_GROUP: admin_users}
        elif ADMIN_GROUP not in user_groups:
            user_groups[ADMIN_GROUP] = admin_users

    if not user_groups:
        if authenticator:
            return authenticator
        return EmptyGroupProvider()

    preconfigured_groups_provider = PreconfiguredGroupProvider(user_groups)
    if not authenticator:
        return preconfigured_groups_provider

    return CombinedGroupProvider(preconfigured_groups_provider, authenticator)


# in case groups will be loaded from ldap
def _exclude_unknown_groups_from_admin_users(admin_users, known_groups):
    if not admin_users or not known_groups:
        return admin_users

    result = []
    for user in admin_users:
        if user.startswith(GROUP_PREFIX):
            group = user[1:]
            if group not in known_groups.keys():
                continue

        result.append(user)

    return result
