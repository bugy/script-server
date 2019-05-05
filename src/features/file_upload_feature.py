import logging
import os

from files.user_file_storage import UserFileStorage
from utils.file_utils import normalize_path

RESULT_FILES_FOLDER = 'uploadFiles'

LOGGER = logging.getLogger('script_server.file_upload_feature')


class FileUploadFeature:
    def __init__(self, user_file_storage: UserFileStorage, temp_folder) -> None:
        self.user_file_storage = user_file_storage
        self.folder = os.path.join(temp_folder, RESULT_FILES_FOLDER)

        user_file_storage.start_autoclean(self.folder, 1000 * 60 * 60 * 24)

    def prepare_new_folder(self, username) -> str:
        new_folder = self.user_file_storage.prepare_new_folder(username, self.folder)
        return normalize_path(new_folder)
