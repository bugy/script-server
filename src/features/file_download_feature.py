import glob
import logging
import os
import re
from shutil import copyfile

import utils.file_utils as file_utils
import utils.os_utils as os_utils
import utils.string_utils as string_utils
from utils.file_utils import create_unique_filename

RESULT_FILES_FOLDER = 'resultFiles'

LOGGER = logging.getLogger('script_server.file_download_feature')


class FileDownloadFeature:
    def __init__(self, user_file_storage, temp_folder) -> None:
        self.user_file_storage = user_file_storage
        self.result_folder = os.path.join(temp_folder, RESULT_FILES_FOLDER)

        user_file_storage.start_autoclean(self.result_folder, 1000 * 60 * 60 * 24)

    def get_result_files_folder(self):
        return self.result_folder

    def prepare_downloadable_files(self, config, script_output, script_param_values, audit_name):
        output_files = config.output_files

        if not output_files:
            return []

        output_files = substitute_parameter_values(
            config.parameters,
            config.output_files,
            script_param_values)

        correct_files = []

        for output_file in output_files:
            files = find_matching_files(output_file, script_output)

            if files:
                for file in files:
                    file_path = file_utils.normalize_path(file, config.get_working_directory())
                    if not os.path.exists(file_path):
                        LOGGER.warning('file ' + file + ' (full path = ' + file_path + ') not found')
                    elif os.path.isdir(file_path):
                        LOGGER.warning('file ' + file + ' is a directory. Not allowed')
                    elif file_path not in correct_files:
                        correct_files.append(file_path)
            else:
                LOGGER.warning("Couldn't find file for " + output_file)

        if not correct_files:
            return []

        download_folder = self.user_file_storage.prepare_new_folder(audit_name, self.result_folder)
        LOGGER.info('Created download folder for ' + audit_name + ': ' + download_folder)

        result = []
        for file in correct_files:
            preferred_download_file = os.path.join(download_folder, os.path.basename(file))

            try:
                download_file = create_unique_filename(preferred_download_file)
            except file_utils.FileExistsException:
                LOGGER.exception('Cannot get unique name')
                continue

            copyfile(file, download_file)

            result.append(download_file)

        return result

    def allowed_to_download(self, file_path, audit_name):
        return self.user_file_storage.allowed_to_access(file_path, audit_name)


def substitute_parameter_values(parameter_configs, output_files, values):
    output_file_parsed = []
    for i, output_file in enumerate(output_files):
        for parameter_config in parameter_configs:
            if parameter_config.secure or parameter_config.no_value:
                continue

            parameter_name = parameter_config.name
            value = values.get(parameter_name)

            if value is None:
                value = ''

            if not isinstance(value, str):
                value = str(value)

            output_file = re.sub('\$\$\$' + parameter_name, value, output_file)

        output_file_parsed.append(output_file)
    return output_file_parsed


def find_matching_files(file_pattern, script_output):
    files = []
    separator = re.escape(os_utils.path_sep())
    output_patterns = [file_pattern]
    while len(output_patterns) > 0:
        output_pattern = output_patterns.pop(0)

        if '#' in output_pattern:
            regex_start = output_pattern.find('#')

            group_number_matches = re.findall('^#\d+#', output_pattern[regex_start:])
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
                    if os_utils.is_linux() or os_utils.is_mac():
                        regex_pattern = '~?' + regex_pattern
                    elif os_utils.is_win():
                        regex_pattern = '(([^\W\d_]:)|~)' + regex_pattern

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
