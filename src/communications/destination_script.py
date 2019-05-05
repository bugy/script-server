import communications.destination_base as destination_base
from model.model_helper import read_obligatory
from utils import process_utils
from utils.string_utils import values_to_string


def _create_communicator(params_dict):
    return ScriptCommunicator(params_dict)


class ScriptDestination(destination_base.Destination):
    def __init__(self, params_dict):
        self._communicator = _create_communicator(params_dict)

    def send(self, title, body, files=None):
        environment_variables = None

        if isinstance(body, dict):
            parameters = list(body.values())
            environment_variables = values_to_string(dict(body))
        elif isinstance(body, list):
            parameters = body
        else:
            raise Exception('Only dict or list bodies are supported')

        parameters = values_to_string(parameters)

        if files:
            raise Exception('Files are not supported for scripts')

        self._communicator.send(parameters, environment_variables=environment_variables)

    def __str__(self, *args, **kwargs):
        return type(self).__name__ + ' for ' + str(self._communicator)


class ScriptCommunicator:
    def __init__(self, params_dict):
        command_config = read_obligatory(params_dict, 'command', ' for Script callback')
        self.command = process_utils.split_command(command_config)

    def send(self, parameters, environment_variables=None):
        full_command = self.command + parameters
        process_utils.invoke(full_command, environment_variables=environment_variables)

    def __str__(self, *args, **kwargs):
        return 'Script: ' + str(self.command)
