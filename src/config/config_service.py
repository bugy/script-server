import json
import logging
import os

from model import script_configs
from utils import os_utils, file_utils

LOGGER = logging.getLogger('config_service')


def _load_script_config(path, content_or_json_dict):
    if isinstance(content_or_json_dict, str):
        json_object = json.loads(content_or_json_dict)
    else:
        json_object = content_or_json_dict
    return script_configs.from_json(path, json_object, os_utils.is_pty_supported())


class ConfigService:
    def __init__(self, conf_folder) -> None:
        self._script_configs_folder = os.path.join(conf_folder, 'runners')
        file_utils.prepare_folder(self._script_configs_folder)

    def list_configs(self):
        def load_script(path, content):
            try:
                json_object = json.loads(content)
                return _load_script_config(path, json_object)
            except:
                LOGGER.exception('Could not load script: ' + path)

        return self.visit_script_configs(load_script)

    def load_config(self, name):
        def find_and_load(path, content):
            try:
                json_object = json.loads(content)

                config_name = script_configs.read_name(path, json_object)
                if config_name == name:
                    return _load_script_config(path, json_object)
            except:
                LOGGER.exception('Could not load script config: ' + path)

        configs = self.visit_script_configs(find_and_load)
        if configs:
            return configs[0]

        return None

    def visit_script_configs(self, visitor):
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

            except:
                LOGGER.exception("Couldn't read the file: " + config_path)

        return result
