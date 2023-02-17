import communications.destination_base as destination_base
from model.model_helper import read_obligatory
from utils import process_utils
from utils.process_utils import ProcessInvoker
from utils.string_utils import values_to_string


def _create_communicator(params_dict, process_invoker):
    return ScriptCommunicator(params_dict, process_invoker)


class ScriptDestination(destination_base.Destination):
    def __init__(self, params_dict, process_invoker: ProcessInvoker):
        self._communicator = _create_communicator(params_dict, process_invoker)

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
    def __init__(self, params_dict, process_invoker: ProcessInvoker):
        command_config = read_obligatory(params_dict, 'command', ' for Script callback')
        self.command = process_utils.split_command(command_config)
        self._process_invoker = process_invoker

    def send(self, parameters, environment_variables=None):
        full_command = self.command + parameters
        self._process_invoker.invoke(full_command, environment_variables=environment_variables)

    def __str__(self, *args, **kwargs):
        return 'Script: ' + str(self.command)
