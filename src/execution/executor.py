import logging
import re
import sys

import model.script_configs
from execution import process_popen, process_base
from model import model_helper
from utils import file_utils, process_utils, os_utils

TIME_BUFFER_MS = 100

LOGGER = logging.getLogger('script_server.ScriptExecutor')

mock_process = False


def create_process_wrapper(executor, command, working_directory):
    run_pty = executor.config.is_requires_terminal()
    if run_pty and not os_utils.is_pty_supported():
        LOGGER.warning(
            "Requested PTY mode, but it's not supported for this OS (" + sys.platform + '). Falling back to POpen')
        run_pty = False

    if run_pty:
        from execution import process_pty
        process_wrapper = process_pty.PtyProcessWrapper(command, working_directory)
    else:
        process_wrapper = process_popen.POpenProcessWrapper(command, working_directory)

    return process_wrapper


_process_creator = create_process_wrapper


class ScriptExecutor:
    def __init__(self, config, parameter_values):
        self.config = config
        self.parameter_values = parameter_values

        self.working_directory = self._get_working_directory()
        self.script_base_command = process_utils.split_command(
            self.config.script_command,
            self.working_directory)
        self.secure_replacements = self.__init_secure_replacements()

        self.process_wrapper = None  # type: process_base.ProcessWrapper
        self.raw_output_stream = None
        self.protected_output_stream = None

    def _get_working_directory(self):
        working_directory = self.config.get_working_directory()
        if working_directory is not None:
            working_directory = file_utils.normalize_path(working_directory)
        return working_directory

    def start(self):
        if self.process_wrapper is not None:
            raise Exception('Executor already started')

        script_args = build_command_args(self.parameter_values, self.config)
        command = self.script_base_command + script_args

        process_wrapper = _process_creator(self, command, self.working_directory)
        process_wrapper.start()

        self.process_wrapper = process_wrapper

        output_stream = process_wrapper.output_stream.time_buffered(TIME_BUFFER_MS, _concat_output)
        self.raw_output_stream = output_stream.replay()

        if self.secure_replacements:
            self.protected_output_stream = output_stream \
                .map(self.__replace_secure_variables) \
                .replay()
        else:
            self.protected_output_stream = self.raw_output_stream

    def __init_secure_replacements(self):
        word_replacements = {}
        for parameter in self.config.parameters:
            if not parameter.secure:
                continue

            value = self.parameter_values.get(parameter.name)
            if model_helper.is_empty(value):
                continue

            if isinstance(value, list):
                elements = value
            else:
                elements = [value]

            for value_element in elements:
                element_string = str(value_element)
                if not element_string.strip():
                    continue

                value_pattern = '\\b' + re.escape(element_string) + '\\b'
                word_replacements[value_pattern] = model_helper.SECURE_MASK

        return word_replacements

    def __replace_secure_variables(self, output):
        result = output

        replacements = self.secure_replacements

        if replacements:
            for word, replacement in replacements.items():
                result = re.sub(word, replacement, result)

        return result

    def get_secure_command(self):
        audit_script_args = build_command_args(
            self.parameter_values,
            self.config,
            model_helper.value_to_str)

        command = self.script_base_command + audit_script_args
        return ' '.join(command)

    def get_anonymized_output_stream(self):
        return self.protected_output_stream

    def get_raw_output_stream(self):
        return self.raw_output_stream

    def get_return_code(self):
        return self.process_wrapper.get_return_code()

    def is_finished(self):
        return self.process_wrapper.is_finished()

    def add_finish_listener(self, listener):
        self.process_wrapper.add_finish_listener(listener)

    def write_to_input(self, text):
        if self.process_wrapper.is_finished():
            LOGGER.warning('process already finished, ignoring input')
            return

        self.process_wrapper.write_to_input(text)

    def kill(self):
        if not self.process_wrapper.is_finished():
            self.process_wrapper.kill()

    def stop(self):
        if not self.process_wrapper.is_finished():
            self.process_wrapper.stop()

    def cleanup(self):
        self.raw_output_stream.dispose()
        self.protected_output_stream.dispose()
        self.process_wrapper.cleanup()


def build_command_args(param_values, config, stringify=lambda value, param: value):
    result = []

    for parameter in config.get_parameters():
        name = parameter.get_name()

        if parameter.is_constant():
            param_values[parameter.name] = model.script_configs.get_default(parameter)

        if name in param_values:
            value = param_values[name]

            if parameter.is_no_value():
                # do not replace == True, since REST service can start accepting boolean as string
                if (value is True) or (value == 'true'):
                    result.append(parameter.get_param())
            elif value:
                if parameter.get_param():
                    result.append(parameter.get_param())

                if parameter.type == 'multiselect':
                    strings = [stringify(element, parameter) for element in value]
                    if parameter.multiple_arguments:
                        result.extend(strings)
                    else:
                        result.append(parameter.separator.join(strings))
                else:
                    value_string = stringify(value, parameter)
                    result.append(value_string)

    return result


def _concat_output(output_chunks):
    if not output_chunks:
        return output_chunks

    return [''.join(output_chunks)]
