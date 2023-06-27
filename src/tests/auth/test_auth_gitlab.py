import unittest
from unittest.mock import patch

# noinspection PyProtectedMember
from tornado.testing import AsyncTestCase, gen_test

# noinspection PyProtectedMember
from auth.auth_abstract_oauth import _OauthUserInfo
from auth.auth_gitlab import GitlabOAuthAuthenticator
from tests.test_utils import AsyncMock


def create_config(*, url=None, group_search=None, group_support=None):
    config = {
        'client_id': '1234',
        'secret': 'hello world?'
    }

    if url is not None:
        config['url'] = url
    if group_search is not None:
        config['group_search'] = group_search
    if group_support is not None:
        config['group_support'] = group_support

    return config


class TestAuthConfig(unittest.TestCase):
    def test_client_visible_config(self):
        authenticator = GitlabOAuthAuthenticator(create_config(url='https://my.gitlab.host'))

        client_visible_config = authenticator._client_visible_config
        self.assertEqual('1234', client_visible_config['client_id'])
        self.assertEqual('https://my.gitlab.host/oauth/authorize', client_visible_config['oauth_url'])
        self.assertEqual('api', client_visible_config['oauth_scope'])

    def test_client_visible_config_when_groups_disabled(self):
        authenticator = GitlabOAuthAuthenticator(create_config(group_support=False))

        client_visible_config = authenticator._client_visible_config
        self.assertEqual('read_user', client_visible_config['oauth_scope'])

    def test_client_visible_config_when_default_url(self):
        authenticator = GitlabOAuthAuthenticator(create_config())

        client_visible_config = authenticator._client_visible_config
        self.assertEqual('https://gitlab.com/oauth/authorize', client_visible_config['oauth_url'])


class TestFetchUserInfo(AsyncTestCase):
    @patch('tornado.auth.OAuth2Mixin.oauth2_request', new_callable=AsyncMock)
    @gen_test
    def test_fetch_user_info(self, mock_request):
        response = {'email': 'me@gmail.com', 'state': 'active'}
        mock_request.return_value = response

        authenticator = GitlabOAuthAuthenticator(create_config(url='https://my.gitlab.host'))

        user_info = yield authenticator.fetch_user_info('my_token_2')
        self.assertEqual(_OauthUserInfo('me@gmail.com', True, response), user_info)

        mock_request.assert_called_with('https://my.gitlab.host/api/v4/user', access_token='my_token_2')

    @patch('tornado.auth.OAuth2Mixin.oauth2_request', new_callable=AsyncMock)
    @gen_test
    def test_fetch_user_info_when_no_response(self, mock_request):
        mock_request.return_value = None

        authenticator = GitlabOAuthAuthenticator(create_config())

        user_info = yield authenticator.fetch_user_info('my_token_2')
        self.assertEqual(None, user_info)

    @patch('tornado.auth.OAuth2Mixin.oauth2_request', new_callable=AsyncMock)
    @gen_test
    def test_fetch_user_info_when_not_active(self, mock_request):
        response = {'email': 'me@gmail.com', 'state': 'something'}
        mock_request.return_value = response

        authenticator = GitlabOAuthAuthenticator(create_config())

        user_info = yield authenticator.fetch_user_info('my_token_2')
        self.assertEqual(_OauthUserInfo('me@gmail.com', False, response), user_info)


class TestFetchUserGroups(AsyncTestCase):
    @patch('tornado.auth.OAuth2Mixin.oauth2_request', new_callable=AsyncMock)
    @gen_test
    def test_fetch_user_groups(self, mock_request):
        response = [{'full_path': 'group1'}, {'full_path': 'group2'}, {'something': 'group3'}]
        mock_request.return_value = response

        authenticator = GitlabOAuthAuthenticator(create_config(url='https://my.gitlab.host'))

        groups = yield authenticator.fetch_user_groups('my_token_2')
        self.assertEqual(['group1', 'group2'], groups)

        mock_request.assert_called_with('https://my.gitlab.host/api/v4/groups',
                                        access_token='my_token_2',
                                        all_available='false',
                                        per_page=100)

    @patch('tornado.auth.OAuth2Mixin.oauth2_request', new_callable=AsyncMock)
    @gen_test
    def test_fetch_user_groups_when_search(self, mock_request):
        mock_request.return_value = []

        authenticator = GitlabOAuthAuthenticator(create_config(url='https://my.gitlab.host', group_search='abc'))

        yield authenticator.fetch_user_groups('my_token_2')

        mock_request.assert_called_with('https://my.gitlab.host/api/v4/groups',
                                        access_token='my_token_2',
                                        all_available='false',
                                        per_page=100,
                                        search='abc')
