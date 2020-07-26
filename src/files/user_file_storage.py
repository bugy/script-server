import datetime
import hashlib
import logging
import os
import re
import shutil
import threading

from utils import file_utils, date_utils
from utils.date_utils import get_current_millis, ms_to_datetime

LOGGER = logging.getLogger('script_server.user_file_storage')


class UserFileStorage:
    def __init__(self, secret) -> None:
        self.secret = secret
        self._autoclean_stopped = False

    def _get_user_download_folder(self, audit_name):
        user_hashed = _hash_user(audit_name, self.secret)
        if len(user_hashed) > 12:
            user_hashed = user_hashed[:12]
        return user_hashed

    def allowed_to_access(self, relative_file_path, user_id):
        user_folder = self._get_user_download_folder(user_id)

        path_chunks = file_utils.split_all(relative_file_path)

        return path_chunks[0] == user_folder

    def prepare_new_folder(self, audit_name, parent_path):
        millis = get_current_millis()
        user_folder_name = self._get_user_download_folder(audit_name)

        temp_path = os.path.join(parent_path, user_folder_name, str(millis))

        file_utils.prepare_folder(temp_path)

        return temp_path

    def start_autoclean(self, parent_folder, lifetime_ms):
        period_sec = lifetime_ms / 1000 / 25

        def clean_results():
            if self._autoclean_stopped:
                return

            if os.path.exists(parent_folder):
                for user_folder in os.listdir(parent_folder):
                    for timed_folder in os.listdir(os.path.join(parent_folder, user_folder)):
                        if not re.match('\d+', timed_folder):
                            continue

                        millis = int(timed_folder)
                        folder_date = ms_to_datetime(millis)
                        now = date_utils.now()

                        if (now - folder_date) > datetime.timedelta(milliseconds=lifetime_ms):
                            folder_path = os.path.join(parent_folder, user_folder, timed_folder)

                            LOGGER.info('Cleaning old folder: ' + folder_path)
                            shutil.rmtree(folder_path)

            timer = threading.Timer(period_sec, clean_results)
            timer.setDaemon(True)
            timer.start()

        timer = threading.Timer(period_sec, clean_results)
        timer.setDaemon(True)
        timer.start()

    def _stop_autoclean(self):
        self._autoclean_stopped = True


def _hash_user(name, secret):
    return hashlib.sha256(name.encode() + secret).hexdigest()
