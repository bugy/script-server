import collections
import logging
import re
import sys

from execution import process_popen, process_base
from model import model_helper
from utils import file_utils, process_utils, os_utils

TIME_BUFFER_MS = 100

LOGGER = logging.getLogger('script_server.ScriptExecutor')

mock_process = False


def create_process_wrapper(executor, command, working_directory):
    run_pty = executor.config.requires_terminal
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


def _normalize_working_dir(working_directory):
    if working_directory is None:
        return None
    return file_utils.normalize_path(working_directory)


def _wrap_values(user_values, parameters):
    result = {}
    for parameter in parameters:
        name = parameter.name

        if parameter.constant:
            value = parameter.default
            result[name] = _Value(None, value, value, parameter.value_to_str(value))
            continue

        if name in user_values:
            user_value = user_values[name]

            if parameter.no_value:
                bool_value = model_helper.read_bool(user_value)
                result[name] = _Value(user_value, bool_value, bool_value, parameter.value_to_str(bool_value))
                continue

            elif user_value:
                mapped_value = parameter.map_to_script(user_value)
                script_arg = parameter.to_script_args(mapped_value)
                result[name] = _Value(user_value, mapped_value, script_arg, parameter.value_to_str(script_arg))
        else:
            result[name] = _Value(None, None, None, '')

    return result


class ScriptExecutor:
    def __init__(self, config, parameter_values):
        self.config = config
        self._parameter_values = _wrap_values(parameter_values, config.parameters)
        self._working_directory = _normalize_working_dir(config.working_directory)

        self.script_base_command = process_utils.split_command(
            self.config.script_command,
            self._working_directory)
        self.secure_replacements = self.__init_secure_replacements()

        self.process_wrapper = None  # type: process_base.ProcessWrapper
        self.raw_output_stream = None
        self.protected_output_stream = None

    def start(self):
        if self.process_wrapper is not None:
            raise Exception('Executor already started')

        script_args = build_command_args(self.get_script_parameter_values(), self.config)
        command = self.script_base_command + script_args

        process_wrapper = _process_creator(self, command, self._working_directory)
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

            value = self._parameter_values.get(parameter.name)
            if value is None:
                continue

            mapped_value = value.mapped_script_value
            if model_helper.is_empty(mapped_value):
                continue

            if isinstance(mapped_value, list):
                elements = mapped_value
            else:
                elements = [mapped_value]

            for value_element in elements:
                element_string = str(value_element)
                if not element_string.strip():
                    continue

                value_pattern = '((?<!\w)|^)' + re.escape(element_string) + '((?!\w)|$)'
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
            {name: str(v) for name, v in self._parameter_values.items()},
            self.config)

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

    def get_user_parameter_values(self):
        return {name: value.user_value
                for name, value in self._parameter_values.items()
                if value.user_value is not None}

    def get_script_parameter_values(self):
        return {name: value.script_arg for name, value in self._parameter_values.items()}

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


def build_command_args(param_values, config):
    result = []

    for parameter in config.parameters:
        name = parameter.name

        if name in param_values:
            value = param_values[name]

            if parameter.no_value:
                if value == True:
                    result.append(parameter.param)

            elif value:
                if parameter.param:
                    result.append(parameter.param)

                if isinstance(value, list):
                    result.extend(value)
                else:
                    result.append(value)

    return result


def _concat_output(output_chunks):
    if not output_chunks:
        return output_chunks

    return [''.join(output_chunks)]


class _Value:
    def __init__(self, user_value, mapped_script_value, script_arg, print_value=None):
        self.user_value = user_value
        self.mapped_script_value = mapped_script_value
        self.script_arg = script_arg
        self.print_value = print_value

    def __str__(self) -> str:
        if self.print_value is not None:
            return self.print_value

        return str(self.script_arg)
