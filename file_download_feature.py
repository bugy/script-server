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
import utils.string_utils as string_utils

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
        files = find_matching_files(output_file, script_output)

        if files:
            for file in files:
                file_path = file_utils.normalize_path(file, config.get_working_directory())
                if not os.path.exists(file_path):
                    logger.warn('file ' + file + ' (full path = ' + file_path + ') not found')
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


def find_matching_files(file_pattern, script_output):
    files = []
    separator = re.escape(os.path.sep)
    output_patterns = [file_pattern]
    while len(output_patterns) > 0:
        output_pattern = output_patterns.pop(0)

        if '#' in output_pattern:
            regex_start = output_pattern.find('#')

            group_number_matches = re.findall('^\#\d+\#', output_pattern[regex_start:])
            if group_number_matches:
                first_match = group_number_matches[0]
                group_number = int(first_match[1:-1])
                pattern_start = regex_start + len(first_match) - 1
            else:
                group_number = 0
                pattern_start = regex_start

            regex_end = output_pattern.find('#', pattern_start + 1)
            while (regex_end >= 0) and output_pattern[regex_end:].startswith('#any_path'):
                regex_end = output_pattern.find('#', regex_end + 1)

            if regex_end >= 0:
                regex_pattern = output_pattern[pattern_start + 1:regex_end]

                if regex_pattern.startswith('#any_path') and (regex_start == 0):
                    if (os.name == 'posix') or (os.name == 'mac'):
                        regex_pattern = '~?' + regex_pattern
                    elif os.name == 'nt':
                        regex_pattern = '[^\W\d_]:\\' + regex_pattern

                regex_pattern = regex_pattern.replace('#any_path', '(' + separator + '([\w.\-]|(\\\ ))+)+')
                found_matches = re.finditer(regex_pattern, script_output)

                for match in found_matches:
                    matched_group = match.group(group_number)
                    new_output_pattern = string_utils.replace(output_pattern, matched_group, regex_start, regex_end)
                    output_patterns.append(new_output_pattern)

                continue

        if '*' not in output_pattern:
            files.append(output_pattern)

        else:
            recursive = '**' in output_pattern
            matching_files = glob.glob(output_pattern, recursive=recursive)
            files.extend(matching_files)

    return files


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
