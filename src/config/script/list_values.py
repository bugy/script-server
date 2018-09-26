import abc
import logging
import re

from model.model_helper import is_empty, fill_parameter_values
from utils import process_utils

LOGGER = logging.getLogger('list_values')


class ValuesProvider(metaclass=abc.ABCMeta):

    def get_required_parameters(self):
        return []

    @abc.abstractmethod
    def get_values(self, parameter_values):
        pass


class EmptyValuesProvider(ValuesProvider):

    def get_values(self, parameter_values):
        return []


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

    def __init__(self, script, parameters) -> None:
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

        parameters_dict = {}
        for parameter in parameters:
            parameters_dict[parameter.name] = parameter

        for param_name in required_parameters:
            if param_name not in parameters_dict:
                raise Exception('Missing parameter "' + param_name + '" for the script')
            parameter = parameters_dict[param_name]
            unsupported_type = None

            if parameter.constant:
                unsupported_type = 'constant'
            elif parameter.secure:
                unsupported_type = 'secure'
            elif parameter.no_value:
                unsupported_type = 'no_value'

            if unsupported_type:
                raise Exception(
                    'Unsupported parameter "' + param_name + '" of type "' + unsupported_type + '" in values.script! ')

        self._required_parameters = tuple(required_parameters)
        self._script_template = script
        self._parameter_configs = parameters

    def get_required_parameters(self):
        return self._required_parameters

    def get_values(self, parameter_values):
        for param_name in self._required_parameters:
            value = parameter_values.get(param_name)
            if is_empty(value):
                return []

        script = fill_parameter_values(self._parameter_configs, self._script_template, parameter_values)

        try:
            script_output = process_utils.invoke(script)
        except:
            LOGGER.exception('Failed to execute script')
            return []

        script_output = script_output.rstrip('\n')
        return script_output.split('\n')
