import abc
import logging
import os
import re

from model.model_helper import is_empty, fill_parameter_values
from config.constants import FILE_TYPE_FILE, FILE_TYPE_DIR
from utils import process_utils

LOGGER = logging.getLogger('list_values')


class ValuesProvider(metaclass=abc.ABCMeta):

    def get_required_parameters(self):
        return []

    @abc.abstractmethod
    def get_values(self, parameter_values):
        pass

    def map_value(self, user_value):
        return user_value


class EmptyValuesProvider(ValuesProvider):

    def get_values(self, parameter_values):
        return []


class NoneValuesProvider(ValuesProvider):

    def get_values(self, parameter_values):
        return None


class ConstValuesProvider(ValuesProvider):

    def __init__(self, values) -> None:
        self._values = tuple(values)

    def get_values(self, parameter_values):
        return self._values


class ScriptValuesProvider(ValuesProvider):

    def __init__(self, script) -> None:
        script_output = process_utils.invoke(script)
        script_output = script_output.rstrip('\n')
        self._values = script_output.split('\n')

    def get_values(self, parameter_values):
        return self._values


class DependantScriptValuesProvider(ValuesProvider):

    def __init__(self, script, parameters_supplier) -> None:
        pattern = re.compile('\${([^}]+)\}')

        search_start = 0
        script_template = ''
        required_parameters = set()

        while search_start < len(script):
            match = pattern.search(script, search_start)
            if not match:
                script_template += script[search_start:]
                break
            param_start = match.start()
            if param_start > search_start:
                script_template += script[search_start:param_start]

            param_name = match.group(1)
            required_parameters.add(param_name)

            search_start = match.end() + 1

        self._required_parameters = tuple(required_parameters)
        self._script_template = script
        self._parameters_supplier = parameters_supplier

    def get_required_parameters(self):
        return self._required_parameters

    def get_values(self, parameter_values):
        for param_name in self._required_parameters:
            value = parameter_values.get(param_name)
            if is_empty(value):
                return []

        parameters = self._parameters_supplier()
        script = fill_parameter_values(parameters, self._script_template, parameter_values)

        try:
            script_output = process_utils.invoke(script)
        except Exception as e:
            LOGGER.warn('Failed to execute script. ' + str(e))
            return []

        script_output = script_output.rstrip('\n')
        return script_output.split('\n')


class FilesProvider(ValuesProvider):

    def __init__(self, file_dir, file_type=None, file_extensions=None) -> None:
        self._values = []
        self._file_dir = file_dir

        if not os.path.exists(file_dir) or not os.path.isdir(file_dir):
            return

        def normalize_extension(extension):
            return re.sub('^\.', '', extension).lower()

        if file_extensions:
            file_extensions = [normalize_extension(ext) for ext in file_extensions]
            file_type = FILE_TYPE_FILE

        sorted_files = sorted(os.listdir(file_dir), key=lambda s: s.casefold())
        for file in sorted_files:
            file_path = os.path.join(file_dir, file)

            if file_type:
                if file_type == FILE_TYPE_DIR and not os.path.isdir(file_path):
                    continue
                elif file_type == FILE_TYPE_FILE and not os.path.isfile(file_path):
                    continue

            if file_extensions:
                _, extension = os.path.splitext(file_path)
                if normalize_extension(extension) not in file_extensions:
                    continue

            self._values.append(file)

    def get_values(self, parameter_values):
        return self._values

    def map_value(self, user_value):
        return os.path.join(self._file_dir, user_value)
