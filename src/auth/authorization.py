from collections import defaultdict

ANY_USER = '__ANY_USER'
ADMIN_GROUP = 'admin_users'
GROUP_PREFIX = '@'


def _normalize_user(user):
    if user:
        return user.lower().strip()
    return user

def _matches_email_domain_pattern(user, pattern):
    if not user or not pattern or not (isinstance(pattern, str) and pattern.startswith('*@')):
        return False

    domain = pattern[1:]  # remove the '*' character
    return user.endswith(domain)


def _normalize_users(allowed_users):
    if isinstance(allowed_users, list):
        if ANY_USER in allowed_users:
            return ANY_USER

        return [_normalize_user(user) for user in allowed_users]

    return allowed_users


class Authorizer:
    def __init__(self, app_allowed_users, admin_users, full_history_users, code_editor_users, groups_provider):
        self._app_allowed_users = _normalize_users(app_allowed_users)
        self._admin_users = _normalize_users(admin_users)
        self._full_history_users = _normalize_users(full_history_users)
        self._code_editor_users = _normalize_users(code_editor_users)

        self._groups_provider = groups_provider

    def is_allowed_in_app(self, user_id):
        return self._is_allowed_internal(user_id, self._app_allowed_users)

    def is_admin(self, user_id):
        return self._is_allowed_internal(user_id, self._admin_users)

    def has_full_history_access(self, user_id):
        return self.is_admin(user_id) or self._is_allowed_internal(user_id, self._full_history_users)

    def can_edit_code(self, user_id):
        return self.is_admin(user_id) and self._is_allowed_internal(user_id, self._code_editor_users)

    def is_allowed(self, user_id, allowed_users):
        normalized_users = _normalize_users(allowed_users)

        return self._is_allowed_internal(user_id, normalized_users)

    def _is_allowed_internal(self, user_id, normalized_allowed_users):
        if not normalized_allowed_users:
            return False

        if normalized_allowed_users == ANY_USER:
            return True

        normalized_user = _normalize_user(user_id)
        
        if normalized_user in normalized_allowed_users:
            return True

        # Check for domain patterns (e.g., "*@mydomain.com")
        for pattern in normalized_allowed_users:
            if _matches_email_domain_pattern(normalized_user, pattern):
                return True

        user_groups = self._groups_provider.get_groups(user_id)
        if not user_groups:
            return False

        for group in user_groups:
            if _normalize_user(GROUP_PREFIX + group) in normalized_allowed_users:
                return True

        return False


class EmptyGroupProvider:

    def get_groups(self, user, known_groups=None):
        return []


def _flatten_groups(groups):
    result = {}

    for group in groups.keys():
        group_members = set()
        visited_groups = set()

        queue = [group]

        while queue:
            current_group = queue.pop()
            if current_group in visited_groups:
                continue
            visited_groups.add(current_group)

            if current_group in result:
                group_members.update(result[current_group])
                continue

            current_group_members = groups[current_group]
            for member in current_group_members:
                group_members.add(member)

                if member.startswith(GROUP_PREFIX) and (member[1:] in groups):
                    queue.append(member[1:])

        result[group] = group_members

    return result


class PreconfiguredGroupProvider:

    def __init__(self, groups) -> None:
        self._user_groups = defaultdict(list)
        self._lazy_group_parents = defaultdict(list)

        flat_groups = _flatten_groups(groups)
        for group, members in flat_groups.items():
            for member in members:
                if member.startswith(GROUP_PREFIX):
                    self._lazy_group_parents[member[1:]].append(group)
                else:
                    self._user_groups[_normalize_user(member)].append(group)

    def get_groups(self, user, known_groups=None):
        user_groups = set(self._user_groups[_normalize_user(user)])

        if known_groups:
            for known_group in known_groups:
                if known_group in self._lazy_group_parents:
                    parent_groups = self._lazy_group_parents[known_group]
                    user_groups.update(parent_groups)

        return user_groups


class CombinedGroupProvider:

    def __init__(self, *other_providers) -> None:
        self._other_providers = list(other_providers)

    def get_groups(self, user, known_groups=None):
        groups = set()

        if not known_groups:
            known_groups = []

        for provider in self._other_providers:
            provider_groups = provider.get_groups(user, known_groups)
            if provider_groups:
                groups.update(provider_groups)
                known_groups.extend(provider_groups)

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

    return CombinedGroupProvider(authenticator, preconfigured_groups_provider)


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


def is_same_user(user_id1, user_id2):
    return _normalize_user(user_id1) == _normalize_user(user_id2)
