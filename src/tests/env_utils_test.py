import os
import unittest

from utils import env_utils
from utils.env_utils import EnvVariables


class TestIsMinVersion(unittest.TestCase):
    def test_2_7_suitable_for_2_1_str(self):
        self.assertTrue(env_utils.is_min_version('2.1', [2, 7]))

    def test_2_7_suitable_for_2_1_float(self):
        self.assertTrue(env_utils.is_min_version(2.1, [2, 7]))

    def test_2_7_suitable_for_2_7_str(self):
        self.assertTrue(env_utils.is_min_version('2.7', [2, 7]))

    def test_2_7_suitable_for_2_7_float(self):
        self.assertTrue(env_utils.is_min_version(2.7, [2, 7]))

    def test_2_6_not_suitable_for_2_7_str(self):
        self.assertFalse(env_utils.is_min_version('2.7', [2, 6]))

    def test_2_6_not_suitable_for_2_7_float(self):
        self.assertFalse(env_utils.is_min_version(2.7, [2, 6]))

    def test_3_5_suitable_for_3_4_str(self):
        self.assertTrue(env_utils.is_min_version('3.4', [3, 5]))

    def test_3_5_suitable_for_3_4_float(self):
        self.assertTrue(env_utils.is_min_version(3.4, [3, 5]))

    def test_3_5_suitable_for_3_5_str(self):
        self.assertTrue(env_utils.is_min_version('3.5', [3, 5]))

    def test_3_5_suitable_for_3_5_float(self):
        self.assertTrue(env_utils.is_min_version(3.5, [3, 5]))

    def test_3_4_not_suitable_for_3_5_str(self):
        self.assertFalse(env_utils.is_min_version('3.5', [3, 4]))

    def test_3_4_not_suitable_for_3_5_float(self):
        self.assertFalse(env_utils.is_min_version(3.5, [3, 4]))

    def test_2_7_not_suitable_for_3_5_str(self):
        self.assertFalse(env_utils.is_min_version('3.5', [2, 7]))

    def test_2_7_not_suitable_for_3_5_float(self):
        self.assertFalse(env_utils.is_min_version(3.5, [2, 7]))

    def test_3_5_not_suitable_for_2_7_str(self):
        self.assertFalse(env_utils.is_min_version('2.7', [3, 5]))

    def test_3_5_not_suitable_for_2_7_float(self):
        self.assertFalse(env_utils.is_min_version(2.7, [3, 5]))

    def test_invalid_version(self):
        self.assertFalse(env_utils.is_min_version('abc', [3, 5]))

    def test_invalid_major_version(self):
        self.assertFalse(env_utils.is_min_version('3a.5', [3, 5]))

    def test_invalid_minor_version(self):
        self.assertFalse(env_utils.is_min_version('3.5b', [3, 5]))


class TestEnvVariables(unittest.TestCase):
    def test_default(self):
        env_vars = EnvVariables(os.environ)
        self.assertEqual(os.getlogin(), env_vars.build_env_vars()['USER'])

    def test_extra_variables(self):
        env_vars = EnvVariables(os.environ)
        all_env_vars = env_vars.build_env_vars(extra_variables={'my_var': 'abcd'})

        self.assertEqual(os.getlogin(), all_env_vars['USER'])
        self.assertEqual('abcd', all_env_vars['my_var'])

    def test_default_extra_variables(self):
        env_vars = EnvVariables(os.environ, extra_variables={'my_var2': 'def'})
        all_env_vars = env_vars.build_env_vars()

        self.assertEqual(os.getlogin(), all_env_vars['USER'])
        self.assertEqual('def', all_env_vars['my_var2'])

    def test_extra_variables_when_collission(self):
        env_vars = EnvVariables(os.environ, extra_variables={'my_var': 'def'})
        all_env_vars = env_vars.build_env_vars(extra_variables={'my_var': 'abcd'})

        self.assertEqual(os.getlogin(), all_env_vars['USER'])
        self.assertEqual('abcd', all_env_vars['my_var'])

    def test_hidden_variables(self):
        env_vars = EnvVariables(os.environ, hidden_variables=['USER'])
        all_env_vars = env_vars.build_env_vars()

        self.assertNotIn('USER', all_env_vars)

    def test_hidden_variables_when_extra(self):
        env_vars = EnvVariables(os.environ, hidden_variables=['USER'])
        all_env_vars = env_vars.build_env_vars(extra_variables={'USER': 'me'})

        self.assertEqual('me', all_env_vars['USER'])

    def test_hidden_variables_when_default_extra(self):
        env_vars = EnvVariables(os.environ, hidden_variables=['USER_EXT'], extra_variables={'USER_EXT': 'me'})
        all_env_vars = env_vars.build_env_vars()

        self.assertNotIn('USER_EXT', all_env_vars)
