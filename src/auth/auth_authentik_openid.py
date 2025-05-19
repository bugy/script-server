import logging

from tornado import escape

from auth.auth_abstract_oauth import AbstractOauthAuthenticator, _OauthUserInfo
from model import model_helper

LOGGER = logging.getLogger('script_server.GoogleOauthAuthorizer')


# noinspection PyProtectedMember
class AuthentikOpenidAuthenticator(AbstractOauthAuthenticator):
    def __init__(self, params_dict):
        authenitk_url = model_helper.read_obligatory(
            params_dict,
            'authenitk_url',
            ': should contain openid url, e.g. http://localhost:9001/')
        if not authenitk_url.endswith('/'):
            authenitk_url = authenitk_url + '/'
        self._authenitk_url = authenitk_url

        super().__init__(authenitk_url + 'application/o/authorize/',
                         authenitk_url + 'application/o/token/',
                         'email openid profile',
                         params_dict)

    async def fetch_user_info(self, access_token) -> _OauthUserInfo:
        user_future = self.http_client.fetch(
            self._authenitk_url + 'application/o/userinfo/',
            headers={'Authorization': 'Bearer ' + access_token})

        user_response = await user_future

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
