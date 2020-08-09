import logging
import re
import sys

from execution import process_popen, process_base
from model import model_helper
from model.model_helper import read_bool
from utils import file_utils, process_utils, os_utils
from utils.transliteration import transliterate

TIME_BUFFER_MS = 100

LOGGER = logging.getLogger('script_server.ScriptExecutor')

mock_process = False


def create_process_wrapper(executor, command, working_directory, env_variables):
    run_pty = executor.config.requires_terminal
    if run_pty and not os_utils.is_pty_supported():
        LOGGER.warning(
            "Requested PTY mode, but it's not supported for this OS (" + sys.platform + '). Falling back to POpen')
        run_pty = False

    if run_pty:
        from execution import process_pty
        process_wrapper = process_pty.PtyProcessWrapper(command, working_directory, env_variables)
    else:
        process_wrapper = process_popen.POpenProcessWrapper(command, working_directory, env_variables)

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
                result[name] = _Value(user_value, bool_value, bool_value)
                continue

            elif user_value:
                mapped_value = parameter.map_to_script(user_value)
                script_arg = parameter.to_script_args(mapped_value)
                secure_value = parameter.get_secured_value(script_arg)
                result[name] = _Value(user_value, mapped_value, script_arg, secure_value)
        else:
            result[name] = _Value(None, None, None)

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

        parameter_values = self.get_script_parameter_values()

        script_args = build_command_args(parameter_values, self.config)
        command = self.script_base_command + script_args
        env_variables = _build_env_variables(parameter_values, self.config.parameters)

        process_wrapper = _process_creator(self, command, self._working_directory, env_variables)
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
            {name: v.get_secure_value() for name, v in self._parameter_values.items()},
            self.config)
        audit_script_args = [str(a) for a in audit_script_args]

        command = self.script_base_command + audit_script_args
        return ' '.join(command)

    def get_anonymized_output_stream(self):
        return self.protected_output_stream

    def get_raw_output_stream(self):
        return self.raw_output_stream

    def get_process_id(self):
        return self.process_wrapper.get_process_id()

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
        option_name = parameter.param
        if parameter.param is None:
            option_name = ''

        if name in param_values:
            value = param_values[name]

            if parameter.no_value:
                if value is True and option_name:
                    result.append(option_name)

            elif value:

                def add_param_and_value(parameter_sh, value_sh):
                    if parameter_sh.param:
                        result.append(parameter_sh.param)
                    if isinstance(value_sh, list):
                        result.extend(value_sh)
                    else:
                        result.append(value_sh)

                if isinstance(value, list):
                    if parameter.same_arg_param:
                        for val in value:
                            if parameter.repeat_param:
                                add_param_and_value(parameter, val)
                            else:
                                result.append(option_name + str(val))
                    else:
                        if parameter.repeat_param:
                            add_param_and_value(parameter, value)
                        else:
                            result.append(option_name + str(value[0]))
                            if len(value) > 1:
                                result.extend(value[1:])
                else:
                    if parameter.repeat_param:
                        add_param_and_value(parameter, value)
                    else:
                        result.append(option_name + str(value))

    return result


def _to_env_name(key):
    transliterated = transliterate(key)
    replaced = re.sub('[^0-9a-zA-Z_]+', '_', transliterated)
    if replaced == '_':
        return None

    return 'PARAM_' + replaced.upper()


def _build_env_variables(parameter_values, parameters):
    result = {}
    excluded = []
    for param_name, value in parameter_values.items():
        if isinstance(value, list) or (value is None):
            continue

        found_parameters = [p for p in parameters if p.name == param_name]
        if len(found_parameters) != 1:
            continue

        parameter = found_parameters[0]

        env_var = parameter.env_var
        if env_var is None:
            env_var = _to_env_name(param_name)

        if (not env_var) or (env_var in excluded):
            continue

        if env_var in result:
            excluded.append(env_var)
            del result[env_var]
            continue

        if parameter.no_value:
            if (value is not None) and (read_bool(value) == True):
                result[env_var] = 'true'
            continue

        result[env_var] = str(value)

    return result


def _concat_output(output_chunks):
    if not output_chunks:
        return output_chunks

    return [''.join(output_chunks)]


class _Value:
    def __init__(self, user_value, mapped_script_value, script_arg, secure_value=None):
        self.user_value = user_value
        self.mapped_script_value = mapped_script_value
        self.script_arg = script_arg
        self.secure_value = secure_value

    def get_secure_value(self):
        if self.secure_value is not None:
            return self.secure_value
        return self.script_arg

    def __str__(self) -> str:
        if self.secure_value is not None:
            return str(self.secure_value)

        return str(self.script_arg)
