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
mock_dump_sessions_to_file = Mock()
mock_do_update_groups = Mock()


class TestAuthConfig(TestCase):
    @patch('time.time', mock_time)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.dump_sessions_to_file', mock_dump_sessions_to_file)
    @patch('auth.auth_gitlab.GitlabOAuthAuthenticator.do_update_groups', mock_do_update_groups)
    def test_gitlab_oauth(self):
        tmp = tempfile.mkstemp('.json', 'test_auth_gitlab-')
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
                "updating": False,
                "updated": now-10,
                "visit": now-10,
                "id": 2,
                "username": "nogroups",
                "name": "John",
                "email": "nogroups@test.com",
                "state": "active"
            }
        }

        os.write(tmp[0], str.encode(escape.json_encode(state)))
        os.fsync(tmp[0])

        config = _from_json({
            'auth': {
                "type": "gitlab",
                "url": "https://gitlab",
                "client_id": "1234",
                "secret": "abcd",
                "group_search": "script-server",
                "ttl": 80,
                "dump": tmp[1],
                "session_expire_min": 1
            },
            'access': {
                 'allowed_users': []
            }})

        self.assertIsInstance(config.authenticator, GitlabOAuthAuthenticator)
        self.assertEqual('1234', config.authenticator.client_id)
        self.assertEqual('abcd', config.authenticator.secret)
        self.assertEqual('https://gitlab', config.authenticator._GITLAB_PREFIX)
        self.assertEqual('script-server', config.authenticator.gitlab_group_search)
        self.assertEqual(80, config.authenticator.gitlab_update)
        self.assertEqual(tmp[1], config.authenticator.gitlab_dump)
        self.assertEqual(60, config.authenticator.session_expire)
        self.assertDictEqual(state, config.authenticator.user_states)
        self.assertEqual(False, config.authenticator.is_active("unknown@test.com"))
        self.assertEqual(False, config.authenticator.is_active("nogroups@test.com"))
        self.assertEqual(True, config.authenticator.is_active("user@test.com"))
        self.assertEqual(time.time(), config.authenticator.user_states["user@test.com"]["visit"])

        # session expire test
        saved_state = config.authenticator.user_states["user@test.com"].copy()
        config.authenticator.user_states["user@test.com"]["visit"] = time.time() - 61
        self.assertEqual(False, config.authenticator.is_active("user@test.com"))
        self.assertEqual(True, mock_dump_sessions_to_file.called)
        mock_dump_sessions_to_file.reset_mock()
        self.assertIsNone(config.authenticator.user_states.get("user@test.com"))
        config.authenticator.user_states["user@test.com"] = saved_state

        self.assertListEqual([], config.authenticator.get_groups("unknown@test.com"))

        # do not update because new
        self.assertListEqual(["testgroup"], config.authenticator.get_groups("user@test.com"))
        self.assertEqual(False, mock_do_update_groups.called)
        mock_do_update_groups.reset_mock()
        # update because old
        config.authenticator.user_states["user@test.com"]["updated"] = time.time() - 81
        self.assertListEqual(["testgroup"], config.authenticator.get_groups("user@test.com"))
        mock_do_update_groups.assert_called_with("user@test.com")
        mock_do_update_groups.reset_mock()
        # do not update because already updating
        config.authenticator.user_states["user@test.com"]["updating"] = True
        self.assertListEqual(["testgroup"], config.authenticator.get_groups("user@test.com"))
        self.assertEqual(False, mock_do_update_groups.called)
        config.authenticator.user_states["user@test.com"]["updating"] = False

        # test clean expire
        saved_state = config.authenticator.user_states["user@test.com"].copy()
        config.authenticator.user_states["user@test.com"]["visit"] = time.time() - 61
        config.authenticator.clean_expired_sessions()
        self.assertIsNone(config.authenticator.user_states.get("user@test.com"))
        config.authenticator.user_states["user@test.com"] = saved_state

        os.close(tmp[0])
        os.unlink(tmp[1])


def _from_json(content):
    json_obj = json.dumps(content)
    conf_path = os.path.join(test_utils.temp_folder, 'conf.json')
    file_utils.write_file(conf_path, json_obj)
    return server_conf.from_json(conf_path, test_utils.temp_folder)