import logging

from tornado import escape
from tornado.httpclient import HTTPClientError

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from auth.auth_base import AuthRejectedError
from model import model_helper

LOGGER = logging.getLogger('script_server.GoogleOauthAuthorizer')


# noinspection PyProtectedMember
class KeycloakOpenidAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        realm_url = model_helper.read_obligatory(
            params_dict,
            'realm_url',
            ': should contain openid realm url, e.g. http://localhost:8080/realms/master')
        if not realm_url.endswith('/'):
            realm_url = realm_url + '/'
        self._realm_url = realm_url

        super().__init__(realm_url + 'protocol/openid-connect/auth',
                         realm_url + 'protocol/openid-connect/token',
                         # "openid" scope is needed since version 20:
                         # https://keycloak.discourse.group/t/issue-on-userinfo-endpoint-at-keycloak-20/18461/2
                         'email openid',
                         params_dict)

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        user_future = self.http_client.fetch(
            self._realm_url + 'protocol/openid-connect/userinfo',
            headers={'Authorization': 'Bearer ' + access_token})

        try:
            user_response = await user_future
        except HTTPClientError as e:
            if e.code == 401:
                raise AuthRejectedError('Failed to fetch user info')
            else:
                raise e

        if not user_response:
            raise Exception('No response during loading userinfo')

        response_values = {}
        if user_response.body:
            response_values = escape.json_decode(user_response.body)

        eager_groups = None
        if self.group_support:
            eager_groups = response_values.get('groups')
            if eager_groups is None:
                eager_groups = []
                LOGGER.warning('Failed to load user groups. Most probably groups mapping is not enabled. '
                               'Check the corresponding wiki section')

        return _OauthUserInfo(response_values.get('preferred_username'), True, response_values, eager_groups)

    async def fetch_user_groups(self, access_token):
        raise Exception('This shouldn\'t be used, all the groups should be fetched with user info.')
