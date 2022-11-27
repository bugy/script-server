import abc
import logging
import re

from model.model_helper import is_empty, fill_parameter_values, InvalidFileException, list_files
from utils.file_utils import FileMatcher
from utils.process_utils import ProcessInvoker

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

    def __init__(self, script, shell, process_invoker: ProcessInvoker) -> None:
        script_output = process_invoker.invoke(script, shell=shell)
        script_output = script_output.rstrip('\n')
        self._values = [line for line in script_output.split('\n') if not is_empty(line)]

    def get_values(self, parameter_values):
        return self._values


class DependantScriptValuesProvider(ValuesProvider):

    def __init__(self, script, parameters_supplier, shell, process_invoker: ProcessInvoker) -> None:
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
        self._shell = shell
        self._process_invoker = process_invoker

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
            script_output = self._process_invoker.invoke(script, shell=self._shell)
        except Exception as e:
            LOGGER.warning('Failed to execute script. ' + str(e))
            return []

        script_output = script_output.rstrip('\n')
        return [line for line in script_output.split('\n') if not is_empty(line)]


class FilesProvider(ValuesProvider):

    def __init__(self,
                 file_dir,
                 file_type=None,
                 file_extensions=None,
                 excluded_files_matcher: FileMatcher = None) -> None:
        self._file_dir = file_dir

        try:
            self._values = list_files(file_dir,
                                      file_type=file_type,
                                      file_extensions=file_extensions,
                                      excluded_files_matcher=excluded_files_matcher)
        except InvalidFileException as e:
            LOGGER.warning('Failed to list files for ' + file_dir + ': ' + str(e))
            self._values = []

    def get_values(self, parameter_values):
        return self._values
