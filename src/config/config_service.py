import json
import logging
import os
import re
from collections import namedtuple
from typing import Union

from auth.authorization import Authorizer
from config.exceptions import InvalidConfigException
from model import script_config
from model.model_helper import InvalidFileException
from model.script_config import get_sorted_config
from utils import os_utils, file_utils, process_utils, custom_json, custom_yaml
from utils.file_utils import to_filename
from utils.string_utils import is_blank, strip

SCRIPT_EDIT_CODE_MODE = 'new_code'
SCRIPT_EDIT_UPLOAD_MODE = 'upload_script'
SCRIPT_EDIT_PATH_MODE = 'new_path'

SCRIPT_PATH_FIELD = 'script_path'
WORKING_DIR_FIELD = 'working_directory'

LOGGER = logging.getLogger('config_service')

ConfigSearchResult = namedtuple('ConfigSearchResult', ['short_config', 'path', 'config_object'])


def _script_name_to_file_name(script_name):
    filename = _escape_characters_in_filename(script_name)
    return filename + '.json'


def _escape_characters_in_filename(script_name):
    escaped = re.sub('[\\s/]+', '_', script_name).strip("_")
    return to_filename(escaped)


def _preprocess_incoming_config(config):
    name = config.get('name')
    if is_blank(name):
        raise InvalidConfigException('Script name is required')
    config['name'] = name.strip()


class ConfigService:
    def __init__(self, authorizer, conf_folder) -> None:
        self._authorizer = authorizer  # type: Authorizer
        self._script_configs_folder = os.path.join(conf_folder, 'runners')
        self._scripts_folder = os.path.join(conf_folder, 'scripts')

        file_utils.prepare_folder(self._script_configs_folder)

    def load_config(self, name, user):
        self._check_admin_access(user)

        search_result = self._find_config(name)

        if search_result is None:
            return None

        (short_config, path, config_object) = search_result

        if config_object.get('name') is None:
            config_object['name'] = short_config.name

        if not self._can_edit_script(user, short_config):
            raise ConfigNotAllowedException(str(user) + ' has no admin access to ' + short_config.name)

        return {'config': config_object, 'filename': os.path.basename(path)}

    def create_config(self, user, config, uploaded_script):
        self._check_admin_access(user)
        _preprocess_incoming_config(config)

        name = config['name']

        search_result = self._find_config(name)
        if search_result is not None:
            raise InvalidConfigException('Another config with the same name already exists')

        self._preprocess_script_fields(config, None, uploaded_script, user)

        path = os.path.join(self._script_configs_folder, _script_name_to_file_name(name))
        unique_path = file_utils.create_unique_filename(path, 100)

        LOGGER.info('Creating new script config "' + name + '" in ' + unique_path)
        self._save_config(config, unique_path)

    def update_config(self, user, config, filename, uploaded_script):
        self._check_admin_access(user)

        _preprocess_incoming_config(config)

        if is_blank(filename):
            raise InvalidConfigException('Script filename should be specified')

        original_file_path = os.path.join(self._script_configs_folder, filename)

        if not os.path.exists(original_file_path):
            raise InvalidFileException(original_file_path, 'Failed to find script path: ' + original_file_path)

        with open(original_file_path, 'r') as f:
            original_config_json = json.load(f)
            short_original_config = script_config.read_short(original_file_path, original_config_json)

        name = config['name']

        search_result = self._find_config(name)
        if (search_result is not None) and (os.path.basename(search_result.path) != filename):
            raise InvalidConfigException('Another script found with the same name: ' + name)

        if not self._can_edit_script(user, short_original_config):
            raise ConfigNotAllowedException(str(user) + ' is not allowed to modify ' + short_original_config.name)

        self._preprocess_script_fields(config, original_config_json, uploaded_script, user)

        LOGGER.info('Updating script config "' + name + '" in ' + original_file_path)
        self._save_config(config, original_file_path)

    def load_script_code(self, script_name, user):
        if not self._authorizer.can_edit_code(user.user_id):
            logging.warning('User ' + str(user) + ' is not allowed to edit code')
            raise InvalidAccessException('Code edit is not allowed for this user')

        config_wrapper = self.load_config(script_name, user)
        if config_wrapper is None:
            return None

        config = config_wrapper.get('config')
        return self._load_script_code_by_config(config)

    def _load_script_code_by_config(self, plain_config):
        script_path = plain_config.get(SCRIPT_PATH_FIELD)
        if is_blank(script_path):
            raise InvalidFileException('', 'Script path is not specified')

        command = process_utils.split_command(script_path, plain_config.get(WORKING_DIR_FIELD))
        binary_files = []
        for argument in command:
            if file_utils.exists(argument):
                if file_utils.is_binary(argument):
                    binary_files.append(argument)
                    continue

                return {'code': file_utils.read_file(argument), 'file_path': argument}

        if binary_files:
            if len(binary_files) == 1:
                return {'code': None, 'file_path': binary_files[0], 'code_edit_error': 'Cannot edit binary file'}

            raise InvalidFileException('command', 'Cannot choose which binary file to edit: ' + str(binary_files))

        if len(command) == 1:
            return {'code': None, 'file_path': command[0], 'code_edit_error': 'Script path does not exist'}

        raise InvalidFileException('command', 'Failed to find script path in command "' + script_path + '"')

    def _save_config(self, config, path):
        sorted_config = get_sorted_config(config)
        config_json = json.dumps(sorted_config, indent=2)
        file_utils.write_file(path, config_json)

    def list_configs(self, user, mode=None):
        edit_mode = mode == 'edit'
        if edit_mode:
            self._check_admin_access(user)

        conf_service = self

        def load_script(path, content):
            try:
                if path.endswith('.yaml'):
                    json_object = custom_yaml.loads(content)
                else:
                    json_object = custom_json.loads(content)
                short_config = script_config.read_short(path, json_object)

                if short_config is None:
                    return None

                if edit_mode and (not conf_service._can_edit_script(user, short_config)):
                    return None

                if (not edit_mode) and (not conf_service._can_access_script(user, short_config)):
                    return None

                return short_config
            except:
                LOGGER.exception('Could not load script: ' + path)

        return self._visit_script_configs(load_script)

    def load_config_model(self, name, user, parameter_values=None, skip_invalid_parameters=False):
        search_result = self._find_config(name)

        if search_result is None:
            return None

        (short_config, path, config_object) = search_result

        if not self._can_access_script(user, short_config):
            raise ConfigNotAllowedException()

        return self._load_script_config(path, config_object, user, parameter_values, skip_invalid_parameters)

    def _visit_script_configs(self, visitor):
        configs_dir = self._script_configs_folder
        files = os.listdir(configs_dir)

        configs = [file for file in files if file.lower().endswith(".json") or file.lower().endswith(".yaml")]

        result = []

        for config_path in configs:
            path = os.path.join(configs_dir, config_path)

            try:
                content = file_utils.read_file(path)

                visit_result = visitor(path, content)
                if visit_result is not None:
                    result.append(visit_result)

            except StopIteration as e:
                if e.value is not None:
                    result.append(e.value)

            except:
                LOGGER.exception("Couldn't read the file: " + config_path)

        return result

    def _find_config(self, name) -> Union[ConfigSearchResult, None]:
        def find_and_load(path, content):
            try:
                if path.endswith('.yaml'):
                    json_object = custom_yaml.loads(content)
                else:
                    json_object = custom_json.loads(content)
                short_config = script_config.read_short(path, json_object)

                if short_config is None:
                    return None
            except:
                LOGGER.exception('Could not load script config: ' + path)
                return None

            if short_config.name != name.strip():
                return None

            raise StopIteration(ConfigSearchResult(short_config, path, json_object))

        configs = self._visit_script_configs(find_and_load)
        if not configs:
            return None

        return configs[0]

    @staticmethod
    def _load_script_config(path, content_or_json_dict, user, parameter_values, skip_invalid_parameters):
        if isinstance(content_or_json_dict, str):
            json_object = custom_json.loads(content_or_json_dict)
        else:
            json_object = content_or_json_dict
        config = script_config.ConfigModel(
            json_object,
            path,
            user.get_username(),
            user.get_audit_name(),
            pty_enabled_default=os_utils.is_pty_supported())

        if parameter_values is not None:
            config.set_all_param_values(parameter_values, skip_invalid_parameters)

        return config

    def _can_access_script(self, user, short_config):
        return self._authorizer.is_allowed(user.user_id, short_config.allowed_users)

    def _can_edit_script(self, user, short_config):
        return self._authorizer.is_allowed(user.user_id, short_config.admin_users)

    def _check_admin_access(self, user):
        if not self._authorizer.is_admin(user.user_id):
            raise AdminAccessRequiredException('Admin access to scripts is prohibited for ' + str(user))

    def _preprocess_script_fields(self, config, original_config_json, uploaded_script, user):
        script_config = config.get('script')
        if not script_config:
            raise InvalidConfigException('script option is required')

        if SCRIPT_PATH_FIELD in config:
            del config[SCRIPT_PATH_FIELD]
        del config['script']

        new_path = strip(script_config.get('path'))
        if is_blank(new_path):
            raise InvalidConfigException('script.path option is required')

        config[SCRIPT_PATH_FIELD] = new_path

        mode = script_config.get('mode')
        if is_blank(mode) or mode == SCRIPT_EDIT_PATH_MODE:
            pass

        elif mode in (SCRIPT_EDIT_UPLOAD_MODE, SCRIPT_EDIT_CODE_MODE):
            if not self._authorizer.can_edit_code(user.user_id):
                raise InvalidAccessException('User ' + str(user) + ' is not allowed to edit code')

            if mode == SCRIPT_EDIT_UPLOAD_MODE:
                if uploaded_script is None:
                    raise InvalidConfigException('Uploaded script should be specified')

            if original_config_json is None:  # new config
                if mode == SCRIPT_EDIT_UPLOAD_MODE:
                    # escaped name is needed, when uploaded file and server has different OSes,
                    # thus different special characters
                    escaped_name = to_filename(uploaded_script.filename)
                    target_path = os.path.join(self._scripts_folder, escaped_name)
                else:
                    filename = os.path.basename(new_path)
                    target_path = os.path.join(self._scripts_folder, _escape_characters_in_filename(filename))

                script_path = file_utils.create_unique_filename(target_path, 100)
                config[SCRIPT_PATH_FIELD] = script_path

            else:
                existing_code = self._load_script_code_by_config(original_config_json)
                script_path = existing_code['file_path']

                if (mode == SCRIPT_EDIT_CODE_MODE) and existing_code.get('code_edit_error') is not None:
                    raise InvalidConfigException('Failed to edit code: ' + existing_code.get('code_edit_error'))

                if new_path != original_config_json.get(SCRIPT_PATH_FIELD):
                    raise InvalidConfigException('script.path override is not allowed for ' + mode + ' mode')

            if mode == SCRIPT_EDIT_UPLOAD_MODE:
                file_utils.write_file(script_path, uploaded_script.body, byte_content=True)
            else:
                code = script_config.get('code')
                if code is None:
                    raise InvalidConfigException('script.code should be specified')
                file_utils.write_file(script_path, code)

            file_utils.make_executable(script_path)

        else:
            raise InvalidConfigException('Unsupported mode: ' + mode)


class ConfigNotAllowedException(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class AdminAccessRequiredException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidAccessException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
