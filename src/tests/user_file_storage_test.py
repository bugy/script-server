import os
import time
import unittest

from files.user_file_storage import UserFileStorage
from tests import test_utils
from utils import file_utils


class TestUserFileStorage(unittest.TestCase):
    def setUp(self):
        test_utils.setup()
        self.storage = UserFileStorage(b'12345678')

    def tearDown(self):
        test_utils.cleanup()
        self.storage._stop_autoclean()

    def test_create_folder(self):
        user_folder = self.storage.prepare_new_folder('me', test_utils.temp_folder)
        self.assertTrue(os.path.exists(user_folder))

    def test_create_folder_for_different_users(self):
        user1_folder = self.storage.prepare_new_folder('user1', test_utils.temp_folder)
        user2_folder = self.storage.prepare_new_folder('user2', test_utils.temp_folder)
        self.assertNotEqual(user1_folder, user2_folder)

    def test_create_different_folders_for_a_user(self):
        folder1 = self.storage.prepare_new_folder('me', test_utils.temp_folder)
        time.sleep(0.002)
        folder2 = self.storage.prepare_new_folder('me', test_utils.temp_folder)
        self.assertNotEqual(folder1, folder2)

    def test_autoclean_folder(self):
        folder = self.storage.prepare_new_folder('me', test_utils.temp_folder)
        self.storage.start_autoclean(test_utils.temp_folder, 2)
        self.assertTrue(os.path.exists(folder))

        time.sleep(0.005)
        self.assertFalse(os.path.exists(folder))

    def test_allow_to_access_own_folder(self):
        user1_folder = self.storage.prepare_new_folder('user1', test_utils.temp_folder)

        relative_folder = file_utils.relative_path(user1_folder, test_utils.temp_folder)
        self.assertTrue(self.storage.allowed_to_access(relative_folder, 'user1'))

    def test_prohibit_access_to_different_user(self):
        user1_folder = self.storage.prepare_new_folder('user1', test_utils.temp_folder)

        relative_folder = file_utils.relative_path(user1_folder, test_utils.temp_folder)
        self.assertFalse(self.storage.allowed_to_access(relative_folder, 'user2'))
