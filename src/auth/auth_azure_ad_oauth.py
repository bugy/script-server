import logging

import tornado.auth

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from model import model_helper

LOGGER = logging.getLogger('script_server.AzureADOauthAuthenticator')


class AzureAdOAuthAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        params_dict['group_support'] = False
        self.auth_url = model_helper.read_obligatory(params_dict, 'auth_url', ' for OAuth')
        self.token_url = model_helper.read_obligatory(params_dict, 'token_url', ' for OAuth')

        super().__init__(
            self.auth_url,
            self.token_url,
            'openid email profile',
            params_dict,
        )

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = await self.http_client.fetch('https://graph.microsoft.com/v1.0/me', headers=headers)
        if not user_response:
            return None

        user_data = tornado.escape.json_decode(user_response.body)
        return _OauthUserInfo(user_data.get('userPrincipalName'), True, user_data)

    async def fetch_user_groups(self, access_token):
        return []
