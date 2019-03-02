import os
import time
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

    def test_prepare_new_folder(self):
        file_path = self.upload_feature.prepare_new_folder('userX')
        self.assertTrue(os.path.exists(file_path))

    def test_prepare_new_folder_different_users(self):
        path1 = self.upload_feature.prepare_new_folder('userX')
        path2 = self.upload_feature.prepare_new_folder('userY')
        self.assertNotEqual(path1, path2)

    def test_prepare_new_folder_twice(self):
        file_path1 = self.upload_feature.prepare_new_folder('userX')
        time.sleep(0.1)
        file_path2 = self.upload_feature.prepare_new_folder('userX')
        self.assertNotEqual(file_path1, file_path2)
