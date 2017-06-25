import unittest

from utils import env_utils


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
