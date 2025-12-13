import logging
from typing import Optional, List, Dict

from tornado import escape

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from model import model_helper

LOGGER = logging.getLogger('script_server.AuthentikOpenidAuthenticator')


def _map_groups(groups: List[str], group_mapping: Optional[Dict[str, str]]) -> List[str]:
    """
    Map Authentik groups to internal groups using the provided mapping.
    Groups not in the mapping are passed through unchanged.
    """
    if not group_mapping:
        return groups

    result = []
    for group in groups:
        if group in group_mapping:
            mapped = group_mapping[group]
            if isinstance(mapped, list):
                result.extend(mapped)
            else:
                result.append(mapped)
        else:
            result.append(group)

    return list(set(result))


# noinspection PyProtectedMember
class AuthentikOpenidAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        # Support both spellings for backwards compatibility
        authentik_url = params_dict.get('authentik_url') or params_dict.get('authentik_url')
        if not authentik_url:
            raise Exception('authentik_url is required: should contain Authentik URL, e.g. https://authentik.example.com/')

        if not authentik_url.endswith('/'):
            authentik_url = authentik_url + '/'
        self._authentik_url = authentik_url

        application_slug = params_dict.get('application_slug')
        if application_slug:
            auth_base = f'{authentik_url}application/o/{application_slug}/'
        else:
            auth_base = f'{authentik_url}application/o/'

        # Read group mapping configuration
        self._group_mapping = model_helper.read_dict(params_dict, 'group_mapping')

        # Read username claim preference
        self._username_claim = params_dict.get('username_claim', 'preferred_username')

        scope = params_dict.get('scope', 'openid email profile groups')

        super().__init__(
            auth_base + 'authorize/',
            auth_base + 'token/',
            scope,
            params_dict)

        # Set userinfo URL
        self._userinfo_url = auth_base + 'userinfo/'

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        user_response = await self.http_client.fetch(
            self._userinfo_url,
            headers={'Authorization': 'Bearer ' + access_token})

        if not user_response:
            raise Exception('No response from Authentik userinfo endpoint')

        response_values = {}
        if user_response.body:
            response_values = escape.json_decode(user_response.body)

        username = response_values.get(self._username_claim)
        if not username:
            for fallback in ['preferred_username', 'email', 'sub']:
                username = response_values.get(fallback)
                if username:
                    if fallback != self._username_claim:
                        LOGGER.warning(
                            f'Username claim "{self._username_claim}" not found, '
                            f'falling back to "{fallback}"')
                    break

        # Extract and map groups
        eager_groups = None
        if self.group_support:
            raw_groups = response_values.get('groups')
            if raw_groups is not None:
                eager_groups = _map_groups(raw_groups, self._group_mapping)
                LOGGER.debug(f'Loaded groups for {username}: {eager_groups}')
            else:
                eager_groups = []
                LOGGER.warning(
                    'Groups not found in Authentik response. '
                    'Make sure the Authentik provider is configured to include groups scope '
                    'and the application has a groups scope mapping.')

        return _OauthUserInfo(username, True, response_values, eager_groups)

    async def fetch_user_groups(self, access_token):
        raise Exception('Groups are fetched with userinfo, this method should not be called')
