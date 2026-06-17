import logging
import os
import re
from shutil import copyfile

import utils.file_utils as file_utils
import utils.os_utils as os_utils
import utils.string_utils as string_utils
from auth.user import User
from execution.execution_service import ExecutionService
from model.model_helper import is_empty, fill_parameter_values, replace_auth_vars
from react.observable import read_until_closed
from utils import audit_utils
from utils.file_utils import create_unique_filename

INLINE_IMAGE_TYPE = 'inline-image'

RESULT_FILES_FOLDER = 'resultFiles'

LOGGER = logging.getLogger('script_server.file_download_feature')


class FileDownloadFeature:
    def __init__(self, user_file_storage, temp_folder) -> None:
        self.user_file_storage = user_file_storage
        self.result_folder = os.path.join(temp_folder, RESULT_FILES_FOLDER)

        user_file_storage.start_autoclean(self.result_folder, 1000 * 60 * 60 * 24)
        self._execution_handlers = {}

    def subscribe(self, execution_service: ExecutionService):
        def start_listener(execution_id, user):
            handler = _ScriptHandler(execution_id, user, execution_service, self.result_folder, self.user_file_storage)
            self._execution_handlers[execution_id] = handler

        execution_service.add_start_listener(start_listener)

    def get_downloadable_files(self, execution_id):
        handler = self._execution_handlers.get(execution_id)
        if not handler:
            return []

        return handler.result_files.copy()

    def get_result_files_folder(self):
        return self.result_folder

    def allowed_to_download(self, file_path, execution_owner):
        return self.user_file_storage.allowed_to_access(file_path, execution_owner)

    def subscribe_on_inline_images(self, execution_id, callback):
        handler = self._execution_handlers.get(execution_id)
        if not handler:
            LOGGER.warn('Failed to find handler for execution #' + execution_id)
            return

        handler.add_inline_image_listener(callback)


class _ScriptHandler:

    def __init__(self, execution_id, user: User, execution_service: ExecutionService, result_folder,
                 file_storage) -> None:
        self.execution_id = execution_id
        self.execution_service = execution_service

        self.config = self.execution_service.get_config(execution_id, user)

        self.result_files_paths = self._get_paths(execution_id, self._is_post_finish_path)
        self.inline_image_paths = self._get_paths(execution_id, self._is_inline_image_path)

        self.prepared_files = {}
        self.result_files = []
        self.inline_images = {}

        self.inline_image_listeners = []

        if not self.result_files_paths and not self.inline_image_paths:
            return

        self.output_stream = self.execution_service.get_anonymized_output_stream(execution_id)

        execution_owner = execution_service.get_owner(execution_id)
        self.download_folder = file_storage.prepare_new_folder(execution_owner, result_folder)
        LOGGER.info('Created download folder for ' + execution_owner + ': ' + self.download_folder)

        if self.result_files_paths:
            execution_service.add_finish_listener(self._execution_finished, execution_id)

        if self.inline_image_paths:
            self._listen_for_images()

    def add_inline_image_listener(self, callback):
        self.inline_image_listeners.append(callback)

    def _get_paths(self, execution_id, predicate):
        config = self.config
        if is_empty(config.output_files):
            return []

        paths = [_extract_path(f) for f in config.output_files if predicate(f)]
        paths = [p for p in paths if p]

        parameter_value_wrappers = config.parameter_values
        all_audit_names = self.execution_service.get_all_audit_names(execution_id)

        audit_name = audit_utils.get_audit_name(all_audit_names)
        username = audit_utils.get_audit_username(all_audit_names)

        return substitute_variable_values(
            config.parameters,
            paths,
            parameter_value_wrappers,
            audit_name,
            username)

    @staticmethod
    def _is_post_finish_path(file):
        if isinstance(file, str):
            return True

        if isinstance(file, dict):
            return file.get('type') != INLINE_IMAGE_TYPE

        return False

    @staticmethod
    def _is_inline_image_path(file):
        return isinstance(file, dict) and file.get('type') == INLINE_IMAGE_TYPE

    def _execution_finished(self):
        output_stream_data = read_until_closed(self.output_stream)
        script_output = ''.join(output_stream_data)

        downloadable_files = self._prepare_downloadable_files(
            self.result_files_paths,
            self.config,
            script_output)

        self.result_files.extend(downloadable_files.values())

    def _listen_for_images(self):
        image_paths = self.inline_image_paths
        script_handler = self

        class InlineImageListener:
            def __init__(self) -> None:
                self.last_buffer = ''

            def on_next(self, output: str):
                output = self.last_buffer + output
                self.last_buffer = ''

                if '\n' not in output:
                    self.last_buffer = output
                    return

                last_newline_index = output.rfind('\n')
                self.last_buffer = output[last_newline_index + 1:]
                output = output[:last_newline_index]

                if output:
                    self.prepare_images(output)

            def on_close(self):
                if not self.last_buffer:
                    return

                self.prepare_images(self.last_buffer)
                self.last_buffer = ''

            @staticmethod
            def prepare_images(output):
                images = script_handler._prepare_downloadable_files(
                    image_paths,
                    script_handler.config,
                    output,
                    should_exist=False)

                for key, value in images.items():
                    script_handler._add_inline_image(key, value)

        self.output_stream.subscribe(InlineImageListener())

    def _prepare_downloadable_files(self, output_files, config, script_output, *, should_exist=True):
        found_files = {}

        for output_file in output_files:
            files = find_matching_files(output_file, script_output)

            if files:
                for file in files:
                    file_path = file_utils.normalize_path(file, config.working_directory)
                    if not os.path.exists(file_path):
                        if should_exist:
                            LOGGER.warning('file ' + file + ' (full path = ' + file_path + ') not found')
                    elif os.path.isdir(file_path):
                        LOGGER.warning('file ' + file + ' is a directory. Not allowed')
                    elif file_path not in found_files:
                        found_files[file] = file_path
            elif should_exist:
                LOGGER.warning("Couldn't find file for " + output_file)

        if not found_files:
            return {}

        result = {}
        for original_file_path, normalized_path in found_files.items():
            if original_file_path in self.prepared_files:
                result[original_file_path] = self.prepared_files[original_file_path]
                continue

            preferred_download_file = os.path.join(self.download_folder, os.path.basename(normalized_path))

            try:
                download_file = create_unique_filename(preferred_download_file)
            except file_utils.FileExistsException:
                LOGGER.exception('Cannot get unique name')
                continue

            copyfile(normalized_path, download_file)

            result[original_file_path] = download_file
            self.prepared_files[original_file_path] = download_file

        return result

    def _add_inline_image(self, original_path, download_path):
        if original_path in self.inline_images:
            return

        self.inline_images[original_path] = download_path

        for listener in self.inline_image_listeners:
            try:
                listener(original_path, download_path)
            except Exception:
                LOGGER.error('Failed to notify image listener')


def substitute_variable_values(parameter_configs, output_files, value_wrappers, audit_name, username):
    output_file_parsed = []
    for _, output_file in enumerate(output_files):
        substituted_file = fill_parameter_values(parameter_configs, output_file, value_wrappers)
        substituted_file = replace_auth_vars(substituted_file, username, audit_name)
        output_file_parsed.append(substituted_file)

    return output_file_parsed


def find_matching_files(file_pattern, script_output):
    files = []
    separator = re.escape(os_utils.path_sep())
    output_patterns = [file_pattern]
    while len(output_patterns) > 0:
        output_pattern = output_patterns.pop(0)

        if '#' in output_pattern:
            regex_start = output_pattern.find('#')

            group_number_matches = re.findall(r'^#\d+#', output_pattern[regex_start:])
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
                        regex_pattern = r'(([^\W\d_]:)|~)' + regex_pattern

                regex_pattern = regex_pattern.replace('#any_path', '(' + separator + r'([\w.\-]|(\\\ ))+)+')
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
            matching_files = file_utils.search_glob(output_pattern, recursive=recursive)
            files.extend(matching_files)

    return files


def _extract_path(output_file):
    if isinstance(output_file, str):
        return output_file
    elif isinstance(output_file, dict):
        path = output_file.get('path')
        if not string_utils.is_blank(path):
            return path.strip()
    return None
