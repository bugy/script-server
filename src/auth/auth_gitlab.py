import logging

from tornado.auth import OAuth2Mixin

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from auth.auth_base import AuthFailureError

LOGGER = logging.getLogger('script_server.GitlabAuthorizer')

_OAUTH_AUTHORIZE_URL = '%s/oauth/authorize'
_OAUTH_ACCESS_TOKEN_URL = '%s/oauth/token'
_OAUTH_GITLAB_USERINFO = '%s/api/v4/user'
_OAUTH_GITLAB_GROUPS = '%s/api/v4/groups'


# noinspection PyProtectedMember
class GitlabOAuthAuthenticator(AbstractOauthAuthenticator, OAuth2Mixin):
    def __init__(self, params_dict):
        self.gitlab_host = params_dict.get('url', 'https://gitlab.com')
        self.gitlab_group_support = params_dict.get('group_support', True)

        super().__init__(
            _OAUTH_AUTHORIZE_URL % self.gitlab_host,
            _OAUTH_ACCESS_TOKEN_URL % self.gitlab_host,
            'api' if self.gitlab_group_support else 'read_user',
            params_dict)

        self.gitlab_group_search = params_dict.get('group_search')

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        user = await self.oauth2_request(
            _OAUTH_GITLAB_USERINFO % self.gitlab_host,
            access_token)
        if user is None:
            return None

        active = user.get('state') == 'active'
        return _OauthUserInfo(user.get('email'), active, user)

    async def fetch_user_groups(self, access_token):
        args = {
            'access_token': access_token,
            'all_available': 'false',
            'per_page': 100,
        }

        if self.gitlab_group_search is not None:
            args['search'] = self.gitlab_group_search

        group_list_future = self.oauth2_request(
            _OAUTH_GITLAB_GROUPS % self.gitlab_host,
            **args
        )

        group_list = await group_list_future

        if group_list is None:
            return None

        groups = []
        for group in group_list:
            if group.get('full_path'):
                groups.append(group['full_path'])

        if groups is None:
            error_message = 'Cant read user groups'
            LOGGER.error(error_message)
            raise AuthFailureError(error_message)

        return groups
