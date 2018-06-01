import logging
import os

from model import script_configs
from utils import os_utils, file_utils

LOGGER = logging.getLogger('config_service')


class ConfigService:
    def __init__(self, conf_folder) -> None:
        self._script_configs_folder = os.path.join(conf_folder, 'runners')
        file_utils.prepare_folder(self._script_configs_folder)

    def list_config_names(self):
        def add_name(path, content):
            try:
                return script_configs.read_name(path, content)

            except:
                LOGGER.exception('Could not load script name: ' + path)

        result = self.visit_script_configs(add_name)

        return result

    def load_config(self, name):
        def find_and_load(path, content):
            try:
                config_name = script_configs.read_name(path, content)
                if config_name == name:
                    return script_configs.from_json(path, content, os_utils.is_pty_supported())
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
