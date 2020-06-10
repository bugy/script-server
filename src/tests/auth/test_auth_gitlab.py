import copy
import json
import os
import tempfile
import time
import unittest

from tornado import escape

from auth.auth_gitlab import GitlabOAuthAuthenticator
from model import server_conf
from tests import test_utils
from utils import file_utils
from unittest import TestCase
from unittest.mock import patch, Mock

if __name__ == '__main__':
    unittest.main()

mock_time = Mock()
mock_time.return_value = 10000.01
mock_persist_session = Mock()
mock_do_update_groups = Mock()
mock_do_update_user = Mock()
mock_request_handler = Mock(**{'get_secure_cookie.return_value': "12345".encode()})


class TestAuthConfig(TestCase):
    @patch('time.time', mock_time)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.persist_session', mock_persist_session)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.do_update_groups', mock_do_update_groups)
    def test_gitlab_oauth(self):
        now = time.time()
        state = {
            "user@test.com": {
                "groups": ["testgroup"],
                "updating": False,
                "updated": now-10,
                "visit": now-10,
                "id": 1,
                "username": "test",
                "name": "John",
                "email": "user@test.com",
                "state": "active"
            },
            "nogroups@test.com": {
                "groups": None,
                "updating": True,
                "updated": now-10,
                "visit": now-10,
                "id": 2,
                "username": "nogroups",
                "name": "John",
                "email": "nogroups@test.com",
                "state": "blocked"
            }
        }

        state_file = test_utils.create_file("gitlab_state.json", text=escape.json_encode(state))

        config = _from_json({
            'auth': {
                "type": "gitlab",
                "url": "https://gitlab",
                "client_id": "1234",
                "secret": "abcd",
                "group_search": "script-server",
                "auth_info_ttl": 80,
                "state_dump_file": state_file,
                "session_expire_minutes": 10
            },
            'access': {
                 'allowed_users': []
            }})

        self.assertIsInstance(config.authenticator, GitlabOAuthAuthenticator)
        self.assertEqual(state_file, config.authenticator.gitlab_dump)
        self.assertEqual("1234", config.authenticator._client_visible_config['client_id'])
        self.assertEqual("https://gitlab/oauth/authorize", config.authenticator._client_visible_config['oauth_url'])
        self.assertEqual("api", config.authenticator._client_visible_config['oauth_scope'])

        assert_state = state.copy()
        for key in list(assert_state.keys()):
            assert_state[key]['updating'] = False
            assert_state[key]['updated'] = 10000.01 - 80 - 1
        self.assertDictEqual(assert_state, config.authenticator.user_states)
        saved_state = copy.deepcopy(config.authenticator.user_states)

        self.assertEqual(False, config.authenticator.validate_user("unknown@test.com", mock_request_handler))
        self.assertEqual(False, config.authenticator.validate_user("nogroups@test.com", mock_request_handler))
        self.assertListEqual([], config.authenticator.get_groups("unknown@test.com"))
        self.assertListEqual([], config.authenticator.get_groups("nogroups@test.com"))

        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(time.time(), config.authenticator.user_states["user@test.com"]["visit"], "visit updated")
        self.assertEqual(True, mock_do_update_groups.called, "state just loaded, gitlab updating")
        mock_do_update_groups.reset_mock()

        config.authenticator.user_states["user@test.com"]["updating"] = True
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(False, mock_do_update_groups.called, "do not call parallel updated")
        mock_do_update_groups.reset_mock()

        mock_time.return_value = 10000.01 + 80*2 + 1  # stale request
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(True, mock_do_update_groups.called, "parallel but stale")
        mock_do_update_groups.reset_mock()
        config.authenticator.user_states = copy.deepcopy(saved_state)
        mock_time.return_value = 10000.01

        config.authenticator.user_states["user@test.com"]['updated'] = now  # gitlab info updated
        config.authenticator.user_states["user@test.com"]['updating'] = False
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(False, mock_do_update_groups.called, "do not update gitlab because ttl not expired")
        mock_do_update_groups.reset_mock()

        mock_time.return_value = 10000.01 + 81
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(True, mock_do_update_groups.called, "ttl expired")
        mock_do_update_groups.reset_mock()
        config.authenticator.user_states = copy.deepcopy(saved_state)
        mock_time.return_value = 10000.01

        # session expire test
        mock_time.return_value = 10000.01 + 601
        self.assertEqual(False, config.authenticator.validate_user("user@test.com", mock_request_handler), "shoud be expired")
        self.assertEqual(True, mock_persist_session.called, "dump state to file")
        mock_persist_session.reset_mock()
        self.assertIsNone(config.authenticator.user_states.get("user@test.com"), "removed from state")
        self.assertListEqual([], config.authenticator.get_groups("user@test.com"))
        config.authenticator.user_states = copy.deepcopy(saved_state)
        mock_time.return_value = 10000.01

        # test clean expire
        mock_time.return_value = 10000.01 + 601
        config.authenticator.clean_sessions()
        self.assertIsNone(config.authenticator.user_states.get("user@test.com"))
        config.authenticator.user_states = copy.deepcopy(saved_state)
        mock_time.return_value = 10000.01

    @patch('time.time', mock_time)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.do_update_user', mock_do_update_user)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.do_update_groups', mock_do_update_groups)
    def test_gitlab_oauth_user_read_scope(self):
        now = time.time()

        state = {
            "user@test.com": {
                "groups": ["testgroup"],
                "updating": False,
                "updated": 0,
                "visit": now-10,
                "id": 1,
                "username": "test",
                "name": "John",
                "email": "user@test.com",
                "state": "active"
            }
        }

        config = _from_json({
            'auth': {
                "type": "gitlab",
                "url": "https://gitlab",
                "client_id": "1234",
                "secret": "abcd",
                "group_search": "script-server",
                "auth_info_ttl": 80,
                "session_expire_minutes": 1,
                "group_support": False
            },
            'access': {
                 'allowed_users': []
            }})

        self.assertIsInstance(config.authenticator, GitlabOAuthAuthenticator)
        self.assertEqual("read_user", config.authenticator._client_visible_config['oauth_scope'])
        config.authenticator.user_states = state
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(False, mock_do_update_groups.called, "update==0, gitlab updating but not groups")
        self.assertEqual(True, mock_do_update_user.called, "update==0, gitlab updating only user")
        mock_do_update_groups.reset_mock()
        mock_do_update_user.reset_mock()

        config.authenticator.gitlab_update = None
        self.assertEqual(True, config.authenticator.validate_user("user@test.com", mock_request_handler))
        self.assertEqual(False, mock_do_update_groups.called, "gitab update disabled")
        self.assertEqual(False, mock_do_update_user.called, "gitab update disabled")
        mock_do_update_groups.reset_mock()
        mock_do_update_user.reset_mock()

    def tearDown(self):
        test_utils.cleanup()


def _from_json(content):
    json_obj = json.dumps(content)
    conf_path = os.path.join(test_utils.temp_folder, 'conf.json')
    file_utils.write_file(conf_path, json_obj)
    return server_conf.from_json(conf_path, test_utils.temp_folder)