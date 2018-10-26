import json
import os
import shutil
import stat
import threading
import uuid

import utils.file_utils as file_utils
import utils.os_utils as os_utils
from execution.process_base import ProcessWrapper
from model.script_configs import ConfigModel, ParameterModel
from react.properties import ObservableDict
from utils import audit_utils

temp_folder = 'tests_temp'


def create_file(filepath):
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    filename = os.path.basename(filepath)
    folder = os.path.join(temp_folder, os.path.dirname(filepath))
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, filename)
    file_utils.write_file(file_path, 'test text')

    return file_path


def setup():
    if os.path.exists(temp_folder):
        _rmtree()

    os.makedirs(temp_folder)


def cleanup():
    if os.path.exists(temp_folder):
        _rmtree()

    os_utils.reset_os()


def _rmtree():
    def on_rm_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)

    shutil.rmtree(temp_folder, onerror=on_rm_error)


def set_linux():
    os_utils.set_linux()


def set_win():
    os_utils.set_win()


def mock_object():
    return type('', (), {})()


def write_script_config(conf_object, filename, config_folder=None):
    if config_folder is None:
        config_folder = os.path.join(temp_folder, 'runners')
    file_path = os.path.join(config_folder, filename + '.json')

    config_json = json.dumps(conf_object)
    file_utils.write_file(file_path, config_json)
    return file_path


def create_script_param_config(
        param_name,
        *,
        type=None,
        default=None,
        required=None,
        secure=None,
        param=None,
        no_value=None,
        constant=None,
        multiselect_separator=None,
        multiple_arguments=None,
        min=None,
        max=None,
        allowed_values=None,
        values_script=None):
    conf = {'name': param_name}

    if type is not None:
        conf['type'] = type

    if values_script is not None:
        conf['values'] = {'script': values_script}

    if default is not None:
        conf['default'] = default

    if required is not None:
        conf['required'] = required

    if secure is not None:
        conf['secure'] = secure

    if param is not None:
        conf['param'] = param

    if no_value is not None:
        conf['no_value'] = no_value

    if constant is not None:
        conf['constant'] = constant

    if multiselect_separator is not None:
        conf['separator'] = multiselect_separator

    if multiple_arguments is not None:
        conf['multiple_arguments'] = multiple_arguments

    if min is not None:
        conf['min'] = min

    if max is not None:
        conf['max'] = max

    if allowed_values is not None:
        conf['values'] = list(allowed_values)

    return conf


def create_config_model(name, *,
                        config=None,
                        username='user1',
                        audit_name='127.0.0.1',
                        path=None,
                        parameters=None,
                        parameter_values=None):
    result_config = {}

    if config:
        result_config.update(config)

    result_config['name'] = name

    if parameters is not None:
        result_config['parameters'] = parameters

    if path is None:
        path = name

    return ConfigModel(result_config, path, username, audit_name, parameter_values=parameter_values)


def create_parameter_model(name=None,
                           *,
                           type=None,
                           values_script=None,
                           default=None,
                           required=None,
                           secure=None,
                           param=None,
                           no_value=None,
                           constant=None,
                           multiselect_separator=None,
                           multiple_arguments=None,
                           min=None,
                           max=None,
                           allowed_values=None,
                           username='user1',
                           audit_name='127.0.0.1',
                           all_parameters=None,
                           other_param_values: ObservableDict = None):
    config = create_script_param_config(
        name,
        type=type,
        values_script=values_script,
        default=default,
        required=required,
        secure=secure,
        param=param,
        no_value=no_value,
        constant=constant,
        multiselect_separator=multiselect_separator,
        multiple_arguments=multiple_arguments,
        min=min,
        max=max,
        allowed_values=allowed_values)

    if all_parameters is None:
        all_parameters = []

    return ParameterModel(config,
                          username,
                          audit_name,
                          lambda: all_parameters,
                          other_param_values=other_param_values)


def create_parameter_model_from_config(config,
                                       *,
                                       username='user1',
                                       audit_name='127.0.0.1',
                                       all_parameters=None):
    if all_parameters is None:
        all_parameters = []

    if config is None:
        config = {}

    return ParameterModel(config, username, audit_name, all_parameters)


def create_audit_names(ip=None, auth_username=None, proxy_username=None, hostname=None):
    result = {}
    if ip is not None:
        result[audit_utils.IP] = ip
    if auth_username is not None:
        result[audit_utils.AUTH_USERNAME] = auth_username
    if proxy_username is not None:
        result[audit_utils.PROXIED_USERNAME] = proxy_username
    if hostname is not None:
        result[audit_utils.HOSTNAME] = hostname
    return result


class _MockProcessWrapper(ProcessWrapper):
    def __init__(self, executor, command, working_directory):
        super().__init__(command, working_directory)

        self.exit_code = None
        self.finished = False
        self.process_id = int.from_bytes(uuid.uuid1().bytes, byteorder='big')
        self.finish_condition = threading.Condition()

    def _get_process_id(self):
        return self.process_id

    # method for tests
    def finish(self, exit_code):
        if self.is_finished():
            raise Exception('Cannot finish a script twice')
        self.__finish(exit_code)

    def stop(self):
        self.__finish(9)

    def kill(self):
        self.__finish(15)

    def __finish(self, exit_code):
        if self.finished:
            return

        with self.finish_condition:
            self.exit_code = exit_code
            self.finished = True
            self.output_stream.close()
            self.finish_condition.notify_all()

        self.notify_finish_thread.join()

    def is_finished(self):
        return self.finished

    def get_return_code(self):
        return self.exit_code

    def pipe_process_output(self):
        pass

    def start_execution(self, command, working_directory):
        pass

    def wait_finish(self):
        with self.finish_condition:
            while not self.finished:
                self.finish_condition.wait(0.01)

    def write_to_input(self, value):
        pass


class AnyUserAuthorizer:
    def is_allowed_in_app(self, user_id):
        return True

    def is_allowed(self, user_id, allowed_users):
        return True

    def is_admin(self, user_id):
        return True
