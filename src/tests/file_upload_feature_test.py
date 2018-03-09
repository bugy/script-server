import os
import unittest

from features.file_upload_feature import FileUploadFeature
from files.user_file_storage import UserFileStorage
from tests import test_utils
from utils import file_utils


class TestUserFileStorage(unittest.TestCase):
    def setUp(self):
        test_utils.setup()
        self.__storage = UserFileStorage(b'12345678')
        self.upload_feature = FileUploadFeature(self.__storage, test_utils.temp_folder)

    def tearDown(self):
        test_utils.cleanup()
        self.__storage._stop_autoclean()

    def test_create_file(self):
        file_path = self.upload_feature.save_file('my_file.txt', b'test text', 'userX')
        self.assertTrue(os.path.exists(file_path))

    def test_content_in_created_file(self):
        file_path = self.upload_feature.save_file('my_file.txt', b'My text', 'userX')
        content = file_utils.read_file(file_path)
        self.assertEqual('My text', content)

    def test_same_filename(self):
        file_path1 = self.upload_feature.save_file('my_file.txt', b'some text', 'userX')
        file_path2 = self.upload_feature.save_file('my_file.txt', b'some text', 'userX')
        self.assertNotEqual(file_path1, file_path2)
