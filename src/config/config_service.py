import json
import logging
import os

from model import script_configs
from utils import os_utils, file_utils

LOGGER = logging.getLogger('config_service')


class ConfigService:
    def __init__(self, authorizer, conf_folder) -> None:
        self._authorizer = authorizer
        self._script_configs_folder = os.path.join(conf_folder, 'runners')

        file_utils.prepare_folder(self._script_configs_folder)

    def list_configs(self, user):
        conf_service = self

        def load_script(path, content):
            try:
                json_object = json.loads(content)
                short_config = script_configs.read_short(path, json_object)

                if short_config is None:
                    return None

                if not conf_service._can_access_script(user, short_config):
                    return None

                return short_config
            except:
                LOGGER.exception('Could not load script: ' + path)

        return self._visit_script_configs(load_script)

    def load_config_model(self, name, user, parameter_values=None):
        def find_and_load(path, content):
            try:
                json_object = json.loads(content)
                short_config = script_configs.read_short(path, json_object)

                if short_config is None:
                    return None
            except:
                LOGGER.exception('Could not load script config: ' + path)
                return None

            if short_config.name != name:
                return None

            raise StopIteration((short_config, path, json_object))

        configs = self._visit_script_configs(find_and_load)
        if not configs:
            return None

        (short_config, path, json_object) = configs[0]

        if not self._can_access_script(user, short_config):
            raise ConfigNotAllowedException()

        return self._load_script_config(path, json_object, user, parameter_values)

    def _visit_script_configs(self, visitor):
        configs_dir = self._script_configs_folder
        files = os.listdir(configs_dir)

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

    def _load_script_config(self, path, content_or_json_dict, user, parameter_values):
        if isinstance(content_or_json_dict, str):
            json_object = json.loads(content_or_json_dict)
        else:
            json_object = content_or_json_dict
        config = script_configs.ConfigModel(
            json_object,
            path,
            user.get_username(),
            user.get_audit_name(),
            pty_enabled_default=os_utils.is_pty_supported(),
            ansi_enabled_default=os_utils.is_linux() or os_utils.is_mac(),
            parameter_values=parameter_values)

        return config

    def _can_access_script(self, user, short_config):
        return self._authorizer.is_allowed(user.user_id, short_config.allowed_users)


class ConfigNotFoundException(Exception):
    def __init__(self, script_name) -> None:
        self.script_name = script_name


class ConfigNotAllowedException(Exception):
    def __init__(self):
        pass
