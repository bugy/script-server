import datetime
import glob
import hashlib
import logging
import os
import re
import shutil
import threading
import time
from shutil import copyfile

import utils.file_utils as file_utils

RESULT_FILES_FOLDER = 'resultFiles'


def hash_user(name, secret_bytes):
    return hashlib.sha256(name.encode() + secret_bytes).hexdigest()


def build_download_path(user_hash, temp_folder):
    millis = int(round(time.time() * 1000))

    return os.path.join(temp_folder, RESULT_FILES_FOLDER, user_hash, str(millis))


def prepare_downloadable_files(config, script_output, audit_name, secret, temp_folder):
    output_files = config.output_files

    if not output_files:
        return []

    logger = logging.getLogger("scriptServer")

    correct_files = []

    for output_file in output_files:
        files = []

        separator = re.escape(os.path.sep)

        if output_file.startswith('#'):
            group_number_matches = re.findall('\#\d+\#', output_file)

            if group_number_matches:
                first_match = group_number_matches[0]
                group_number = int(first_match[1:-1])
                pattern = output_file[len(first_match):]
            else:
                group_number = 0
                pattern = output_file[1:]

            if pattern.startswith('#any_path'):
                if (os.name == 'posix') or (os.name == 'mac'):
                    pattern = '~?' + pattern
                elif os.name == 'nt':
                    pattern = '[^\W\d_]:\\' + pattern

            pattern = pattern.replace('#any_path', '(' + separator + '[^' + separator + ']+)*?')

            found_matches = re.finditer(pattern, script_output)

            for match in found_matches:
                files.append(match.group(group_number))

        elif '*' not in output_file:
            files.append(output_file)

        else:
            recursive = '**' in output_file
            matching_files = glob.glob(output_file, recursive=recursive)
            files.extend(matching_files)

        if files:
            for file in files:
                file_path = file_utils.normalize_path(file, config.get_working_directory())
                if not os.path.exists(file_path):
                    logger.warn('file ' + file + '(' + file_path + ') not found')
                elif os.path.isdir(file_path):
                    logger.warn('file ' + file + ' is a directory. Not allowed')
                elif file_path not in correct_files:
                    correct_files.append(file_path)
        else:
            logger.warn("Couldn't find file for " + output_file)

    if not correct_files:
        return []

    user_hashed = get_user_download_folder(audit_name, secret)

    download_folder = build_download_path(user_hashed, temp_folder)
    logger.info('Created download folder for ' + audit_name + ': ' + download_folder)

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    result = []
    for file in correct_files:
        download_file = os.path.join(download_folder, os.path.basename(file))

        if os.path.exists(download_file):
            i = 0

            filename_split = os.path.splitext(os.path.basename(file))
            extension = ''
            name = ''
            if len(filename_split) > 0:
                name = filename_split[0]
                if len(filename_split) > 1:
                    extension = filename_split[1]

            while os.path.exists(download_file) and i < 1000:
                download_file = os.path.join(download_folder, name + '_' + str(i) + extension)
                i += 1

            if os.path.exists(download_file):
                logger.warn("Couldn't create unique filename for " + file)
                continue

        copyfile(file, download_file)

        result.append(download_file)

    return result


def get_user_download_folder(audit_name, secret):
    user_hashed = hash_user(audit_name, secret)
    if len(user_hashed) > 12:
        user_hashed = user_hashed[:12]
    return user_hashed


def allowed_to_download(file_path, audit_name, secret_bytes):
    user_folder = get_user_download_folder(audit_name, secret_bytes)

    path_chunks = file_utils.split_all(file_path)

    return path_chunks[0] == user_folder


def get_result_files_folder(temp_folder):
    return os.path.join(temp_folder, RESULT_FILES_FOLDER)


def autoclean_downloads(temp_folder):
    results_folder = get_result_files_folder(temp_folder)

    logger = logging.getLogger('scriptServer')

    delay_secs = 60.0 * 60

    def clean_results():
        if os.path.exists(results_folder):
            for user_folder in os.listdir(results_folder):
                for timed_folder in os.listdir(os.path.join(results_folder, user_folder)):
                    if not re.match('\d+', timed_folder):
                        continue

                    millis = int(timed_folder)
                    folder_date = datetime.datetime.fromtimestamp(millis / 1000.0)
                    now = datetime.datetime.now()

                    if (now - folder_date) > datetime.timedelta(hours=24):
                        folder_path = os.path.join(results_folder, user_folder, timed_folder)

                        logger.info('Cleaning old download folder: ' + folder_path)
                        shutil.rmtree(folder_path)

        timer = threading.Timer(delay_secs, clean_results)
        timer.setDaemon(True)
        timer.start()

    timer = threading.Timer(delay_secs, clean_results)
    timer.setDaemon(True)
    timer.start()
