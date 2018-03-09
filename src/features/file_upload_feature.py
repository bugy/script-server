import logging
import os

from files.user_file_storage import UserFileStorage
from utils import file_utils

RESULT_FILES_FOLDER = 'uploadFiles'

LOGGER = logging.getLogger('script_server.file_upload_feature')


class FileUploadFeature:
    def __init__(self, user_file_storage: UserFileStorage, temp_folder) -> None:
        self.user_file_storage = user_file_storage
        self.folder = os.path.join(temp_folder, RESULT_FILES_FOLDER)

        user_file_storage.start_autoclean(self.folder, 1000 * 60 * 60 * 24)

    def save_file(self, filename, body, username) -> str:
        upload_folder = self.user_file_storage.prepare_new_folder(username, self.folder)
        result_path = os.path.join(upload_folder, filename)

        file_utils.write_file(result_path, body, True)

        return file_utils.normalize_path(result_path)
