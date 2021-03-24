import json
import logging
import os
import re

from config.exceptions import InvalidConfigException
from model import script_config
from model.model_helper import InvalidFileException
from model.script_config import get_sorted_config
from utils import os_utils, file_utils
from utils.file_utils import to_filename
from utils.string_utils import is_blank

LOGGER = logging.getLogger('config_service')


def _script_name_to_file_name(script_name):
    escaped_whitespaces = re.sub('[\\s/]+', '_', script_name).strip("_")
    filename = to_filename(escaped_whitespaces)
    return filename + '.json'


def _preprocess_incoming_config(config):
    name = config.get('name')
    if is_blank(name):
        raise InvalidConfigException('Script name is required')
    config['name'] = name.strip()

    script_path = config.get('script_path')
    if is_blank(script_path):
        raise InvalidConfigException('Script path is required')
    config['script_path'] = script_path.strip()


class ConfigService:
    def __init__(self, authorizer, conf_folder) -> None:
        self._authorizer = authorizer
        self._script_configs_folder = os.path.join(conf_folder, 'runners')

        file_utils.prepare_folder(self._script_configs_folder)

    def load_config(self, name, user):
        self._check_admin_access(user)

        (short_config, path, config_object) = self._find_config(name)

        if path is None:
            return None

        if config_object.get('name') is None:
            config_object['name'] = short_config.name

        if not self._can_edit_script(user, short_config):
            raise ConfigNotAllowedException(str(user) + ' has no admin access to ' + short_config.name)

        return {'config': config_object, 'filename': os.path.basename(path)}

    def create_config(self, user, config):
        self._check_admin_access(user)
        _preprocess_incoming_config(config)

        name = config['name']

        (short_config, path, json_object) = self._find_config(name)
        if path is not None:
            raise InvalidConfigException('Another config with the same name already exists')

        path = os.path.join(self._script_configs_folder, _script_name_to_file_name(name))
        unique_path = file_utils.create_unique_filename(path, 100)

        LOGGER.info('Creating new script config "' + name + '" in ' + unique_path)
        self._save_config(config, unique_path)

    def update_config(self, user, config, filename):
        self._check_admin_access(user)
        _preprocess_incoming_config(config)

        if is_blank(filename):
            raise InvalidConfigException('Script filename should be specified')

        original_file_path = os.path.join(self._script_configs_folder, filename)
        if not os.path.exists(original_file_path):
            raise InvalidFileException(original_file_path, 'Failed to find script path: ' + original_file_path)

        name = config['name']

        (short_config, found_config_path, json_object) = self._find_config(name)
        if (found_config_path is not None) and (os.path.basename(found_config_path) != filename):
            raise InvalidConfigException('Another script found with the same name: ' + name)

        if (short_config is not None) and not self._can_edit_script(user, short_config):
            raise ConfigNotAllowedException(str(user) + ' is not allowed to modify ' + short_config.name)

        LOGGER.info('Updating script config "' + name + '" in ' + original_file_path)
        self._save_config(config, original_file_path)

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
                json_object = json.loads(content)
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
        (short_config, path, json_object) = self._find_config(name)

        if path is None:
            return None

        if not self._can_access_script(user, short_config):
            raise ConfigNotAllowedException()

        return self._load_script_config(path, json_object, user, parameter_values, skip_invalid_parameters)

    def _visit_script_configs(self, visitor):
        configs_dir = self._script_configs_folder

        files=[]
        # Read config file from within directories too
        for _root, _dirs, _files in os.walk(configs_dir, topdown=True):
            for name in _files:
                files.append( os.path.join(_root, name).replace( 'conf/runners/', '') )

        configs = [file for file in files if file.lower().endswith(".json")]

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

    def _find_config(self, name):
        def find_and_load(path, content):
            try:
                json_object = json.loads(content)
                short_config = script_config.read_short(path, json_object)

                if short_config is None:
                    return None
            except:
                LOGGER.exception('Could not load script config: ' + path)
                return None

            if short_config.name != name.strip():
                return None

            raise StopIteration((short_config, path, json_object))

        configs = self._visit_script_configs(find_and_load)
        if not configs:
            return None, None, None

        return configs[0]

    def _load_script_config(self, path, content_or_json_dict, user, parameter_values, skip_invalid_parameters):
        if isinstance(content_or_json_dict, str):
            json_object = json.loads(content_or_json_dict)
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


class ConfigNotAllowedException(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class AdminAccessRequiredException(Exception):
    def __init__(self, message):
        super().__init__(message)


