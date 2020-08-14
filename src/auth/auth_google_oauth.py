import logging

import tornado.auth

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo

LOGGER = logging.getLogger('script_server.GoogleOauthAuthorizer')


# noinspection PyProtectedMember
class GoogleOauthAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        params_dict['group_support'] = False

        super().__init__(tornado.auth.GoogleOAuth2Mixin._OAUTH_AUTHORIZE_URL,
                         tornado.auth.GoogleOAuth2Mixin._OAUTH_ACCESS_TOKEN_URL,
                         'email',
                         params_dict)

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        oauth_mixin = tornado.auth.GoogleOAuth2Mixin()
        user_future = oauth_mixin.oauth2_request(
            tornado.auth.GoogleOAuth2Mixin._OAUTH_USERINFO_URL,
            access_token=access_token)
        user_response = await user_future
        if not user_response:
            return None

        return _OauthUserInfo(user_response.get('email'), True, user_response)

    async def fetch_user_groups(self, access_token):
        return []
