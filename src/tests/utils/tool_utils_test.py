import unittest

from tests import test_utils
from utils.tool_utils import get_server_version


class TestGetVersion(unittest.TestCase):
    def test_get_version_when_valid(self):
        test_utils.create_file('version.txt', text='1.14.0')
        version = get_server_version(test_utils.temp_folder)
        self.assertEqual('1.14.0', version)

    def test_get_version_when_no_file(self):
        version = get_server_version(test_utils.temp_folder)
        self.assertIsNone(version)

    def test_get_version_when_no_content(self):
        test_utils.create_file('my_file.txt', text='')
        version = get_server_version(test_utils.temp_folder)
        self.assertIsNone(version)

    def tearDown(self):
        test_utils.cleanup()
