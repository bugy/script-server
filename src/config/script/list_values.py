import abc
import logging
import re

from model.model_helper import is_empty, fill_parameter_values, InvalidFileException, list_files
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

class DependantValuesProvider(ValuesProvider):
    def __init__(self, variable_name, values_conditions, parameters_supplier) -> None:
        self._values_conditions = values_conditions
        self._required_parameters = set()
        self._var_name = variable_name
        self._availible_values = set()
        self._possible_values = set()

        if not isinstance(self._values_conditions, dict):
            raise Exception(f"The given value of {self._var_name} isn't acceptable (dictionary) type\n\t{self._values_conditions}")
        
        try:
            for e in self._values_conditions:
                self._possible_values.add(e)
                for key in self._values_conditions[e]:
                    self._required_parameters.add(key)

        except Exception as ex:
            raise Exception(f"Exception {ex} during process{self._var_name}")

    def get_required_parameters(self):
        return self._required_parameters

    def get_values(self, parameter_values):
        self._availible_values = set()
        deny_values = set()

        for e in self._values_conditions:
            for key in self._values_conditions[e]:
                pvalue = parameter_values.get(key)                
                if not is_empty(pvalue):
                    if not(pvalue in self._values_conditions[e][key] ):
                        deny_values.add(e)
        
        self._availible_values = self._possible_values.difference(deny_values)
        return list(self._availible_values)

    def map_value(self, user_value):
        return user_value if user_value in self._availible_values else None


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
            LOGGER.warning('Failed to execute script. ' + str(e))
            return []

        script_output = script_output.rstrip('\n')
        return script_output.split('\n')


class FilesProvider(ValuesProvider):

    def __init__(self, file_dir, file_type=None, file_extensions=None) -> None:
        self._file_dir = file_dir

        try:
            self._values = list_files(file_dir, file_type, file_extensions)
        except InvalidFileException as e:
            LOGGER.warning('Failed to list files for ' + file_dir + ': ' + str(e))
            self._values = []

    def get_values(self, parameter_values):
        return self._values
