import json
import os
import shutil
import stat
import threading
import uuid
from copy import copy
from unittest.case import TestCase
from unittest.mock import MagicMock

import utils.file_utils as file_utils
import utils.os_utils as os_utils
from auth.auth_base import Authenticator, AuthRejectedError
from execution.process_base import ProcessWrapper
from model.script_config import ConfigModel, ParameterModel
from model.server_conf import LoggingConfig
from react.observable import read_until_closed
from react.properties import ObservableDict
from utils import audit_utils
from utils.env_utils import EnvVariables
from utils.process_utils import ProcessInvoker

temp_folder = 'tests_temp'
_original_env = {}

_hidden_variables = ['MY_PASSWORD', 'SOME_SECRET']
env_variables = EnvVariables(os.environ, hidden_variables=_hidden_variables)
process_invoker = ProcessInvoker(env_variables)


def create_file(filepath, *, overwrite=False, text='test text'):
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    filename = os.path.basename(filepath)
    folder = os.path.join(temp_folder, os.path.dirname(filepath))
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path) and not overwrite:
        raise Exception('File ' + file_path + ' already exists')

    file_utils.write_file(file_path, text)

    return file_path


def create_files(names, dir=None):
    for name in names:
        if dir is not None:
            create_file(os.path.join(dir, name))
        else:
            create_file(name)


def create_dir(dir_path):
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    full_path = os.path.join(temp_folder, dir_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    return full_path


def setup():
    if os.path.exists(temp_folder):
        _rmtree(temp_folder)

    os.makedirs(temp_folder)


def cleanup():
    if os.path.exists(temp_folder):
        _rmtree(temp_folder)

    os_utils.reset_os()

    for key, value in _original_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value

    _original_env.clear()


def _rmtree(folder):
    exception = None

    def on_rm_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)
            os.remove(path)
        except Exception as e:
            print('Failed to remove path ' + path + ': ' + str(e))
            nonlocal exception
            if exception is None:
                exception = e

    shutil.rmtree(folder, onerror=on_rm_error)
    if exception:
        raise exception


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
        env_var=None,
        no_value=None,
        constant=None,
        multiselect_separator=None,
        multiselect_argument_type=None,
        min=None,
        max=None,
        allowed_values=None,
        values_script=None,
        file_dir=None,
        file_recursive=None,
        file_type=None,
        file_extensions=None,
        excluded_files=None,
        same_arg_param=None,
        values_script_shell=None,
        max_length=None,
        regex=None):
    conf = {'name': param_name}

    if type is not None:
        conf['type'] = type

    if values_script is not None:
        conf['values'] = {'script': values_script}
        if values_script_shell is not None:
            conf['values']['shell'] = values_script_shell

    if default is not None:
        conf['default'] = default

    if required is not None:
        conf['required'] = required

    if secure is not None:
        conf['secure'] = secure

    if param is not None:
        conf['param'] = param

    if env_var is not None:
        conf['env_var'] = env_var

    if no_value is not None:
        conf['no_value'] = no_value

    if constant is not None:
        conf['constant'] = constant

    if multiselect_separator is not None:
        conf['separator'] = multiselect_separator

    if multiselect_argument_type is not None:
        conf['multiselect_argument_type'] = multiselect_argument_type

    if min is not None:
        conf['min'] = min

    if max is not None:
        conf['max'] = max

    if allowed_values is not None:
        conf['values'] = list(allowed_values)

    if file_dir is not None:
        conf['file_dir'] = file_dir

    if file_recursive is not None:
        conf['file_recursive'] = file_recursive

    if file_extensions is not None:
        conf['file_extensions'] = file_extensions

    if file_type is not None:
        conf['file_type'] = file_type

    if excluded_files is not None:
        conf['excluded_files'] = excluded_files

    if same_arg_param is not None:
        conf['same_arg_param'] = same_arg_param

    if regex is not None:
        conf['regex'] = regex

    if max_length is not None:
        conf['max_length'] = max_length

    return conf


def create_config_model(name, *,
                        config=None,
                        username='user1',
                        audit_name='127.0.0.1',
                        path=None,
                        parameters=None,
                        parameter_values=None,
                        script_command='ls',
                        output_files=None,
                        requires_terminal=None,
                        schedulable=True,
                        logging_config: LoggingConfig = None,
                        output_format=None):
    result_config = {}

    if config:
        result_config.update(config)

    result_config['name'] = name

    if parameters is not None:
        result_config['parameters'] = parameters

    if path is None:
        path = name

    if output_files is not None:
        result_config['output_files'] = output_files

    if requires_terminal is not None:
        result_config['requires_terminal'] = requires_terminal

    if schedulable is not None:
        result_config['scheduling'] = {'enabled': schedulable}

    if output_format:
        result_config['output_format'] = output_format

    if logging_config is not None:
        result_config['logging'] = {
            'execution_file': logging_config.filename_pattern,
            'execution_date_format': logging_config.date_format}

    result_config['script_path'] = script_command

    model = ConfigModel(result_config, path, username, audit_name, process_invoker)
    if parameter_values is not None:
        model.set_all_param_values(model)

    return model


def create_parameter_model(name=None,
                           *,
                           type=None,
                           values_script=None,
                           default=None,
                           required=None,
                           secure=None,
                           param=None,
                           env_var=None,
                           no_value=None,
                           constant=None,
                           multiselect_separator=None,
                           multiselect_argument_type=None,
                           min=None,
                           max=None,
                           allowed_values=None,
                           username='user1',
                           audit_name='127.0.0.1',
                           all_parameters=None,
                           file_dir=None,
                           file_recursive=None,
                           other_param_values: ObservableDict = None,
                           values_script_shell=None,
                           max_length=None,
                           regex=None):
    config = create_script_param_config(
        name,
        type=type,
        values_script=values_script,
        default=default,
        required=required,
        secure=secure,
        param=param,
        env_var=env_var,
        no_value=no_value,
        constant=constant,
        multiselect_separator=multiselect_separator,
        multiselect_argument_type=multiselect_argument_type,
        min=min,
        max=max,
        allowed_values=allowed_values,
        file_dir=file_dir,
        file_recursive=file_recursive,
        values_script_shell=values_script_shell,
        max_length=max_length,
        regex=regex)

    if all_parameters is None:
        all_parameters = []

    return ParameterModel(config,
                          username,
                          audit_name,
                          lambda: all_parameters,
                          other_param_values=other_param_values,
                          process_invoker=process_invoker)


def create_simple_parameter_configs(names):
    return {name: {'name': name} for name in names}


def create_parameter_model_from_config(config,
                                       *,
                                       username='user1',
                                       audit_name='127.0.0.1',
                                       working_dir=None,
                                       all_parameters=None):
    if all_parameters is None:
        all_parameters = []

    if config is None:
        config = {}

    return ParameterModel(
        config,
        username,
        audit_name,
        all_parameters,
        working_dir=working_dir,
        process_invoker=process_invoker)


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


class CustomEnvScope:
    def __init__(self, key_values) -> None:
        self._key_values = key_values
        self._original_process_invoker = process_invoker
        self._original_env_vars = env_variables

    def __enter__(self):
        global env_variables
        global process_invoker
        global _hidden_variables
        env_variables = EnvVariables(os.environ, extra_variables=self._key_values, hidden_variables=_hidden_variables)
        process_invoker = ProcessInvoker(env_variables)
        return self

    def __exit__(self, type, value, traceback):
        global env_variables
        global process_invoker
        env_variables = self._original_env_vars
        process_invoker = self._original_process_invoker


def custom_env(*args):
    if len(args) == 0:
        raise Exception('No env variables are specified')

    if len(args) == 1 and isinstance(args[0], dict):
        key_values = args[0]
    elif len(args) % 2 != 0:
        raise Exception('Even number of arguments is expected')
    else:
        key_values = {args[i]: args[i + 1] for i in range(0, len(args), 2)}

    return CustomEnvScope(key_values)


def set_os_environ_value(key, value):
    if key not in _original_env:
        if key in os.environ:
            _original_env[key] = value
        else:
            _original_env[key] = None

    os.environ[key] = value


def assert_large_dict_equal(expected, actual, testcase):
    if len(expected) < 20 and len(actual) < 20:
        testcase.assertEqual(expected, actual)
        return

    if expected == actual:
        return

    diff_expected = {}
    diff_actual = {}
    too_large_diff = False

    all_keys = set()
    all_keys.update(expected.keys())
    all_keys.update(actual.keys())
    for key in all_keys:
        expected_value = expected.get(key)
        actual_value = actual.get(key)

        if expected_value == actual_value:
            continue

        diff_expected[key] = expected_value
        diff_actual[key] = actual_value

        if len(diff_expected) >= 50:
            too_large_diff = True
            break

    message = 'Showing only different elements'
    if too_large_diff:
        message += ' (limited to 50)'

    testcase.assertEqual(diff_expected, diff_actual, message)


def wait_observable_close_notification(observable, timeout):
    close_condition = threading.Event()
    observable.subscribe_on_close(lambda: close_condition.set())
    close_condition.wait(timeout)


def mock_request_handler(*, arguments: dict = None, method='GET', headers=None):
    if headers is None:
        headers = {}

    request_handler = mock_object()

    def get_argument(arg_name):
        if arguments is None:
            return None
        return arguments.get(arg_name)

    request_handler.get_argument = get_argument

    request_handler.request = mock_object()
    request_handler.request.method = method
    request_handler.request.headers = headers

    return request_handler


def assert_dir_files(expected_files, dir_path, test_case: TestCase):
    expected_files_sorted = sorted(copy(expected_files))
    actual_files = sorted(os.listdir(dir_path))

    test_case.assertSequenceEqual(expected_files_sorted, actual_files)


def assert_contains_sub_dict(test_case: TestCase, big_dict: dict, sub_dict: dict):
    for key_value in sub_dict.items():
        if key_value not in big_dict.items():
            test_case.fail(repr(big_dict) + ' does not contain ' + repr(sub_dict))


def wait_and_read(process_wrapper):
    thread = threading.Thread(target=process_wrapper.wait_finish, daemon=True)
    thread.start()
    thread.join(timeout=0.1)

    return ''.join(read_until_closed(process_wrapper.output_stream))


class _MockProcessWrapper(ProcessWrapper):
    def __init__(self, executor, command, working_directory, env_variables):
        super().__init__(command, working_directory, env_variables)

        self.exit_code = None
        self.finished = False
        self.process_id = int.from_bytes(uuid.uuid1().bytes, byteorder='big')
        self.finish_condition = threading.Condition()

    def get_process_id(self):
        return self.process_id

    # method for tests
    def finish(self, exit_code):
        if self.is_finished():
            raise Exception('Cannot finish a script twice')
        self.__finish(exit_code)

    # method for tests
    def write_output(self, output):
        self._write_script_output(output)

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


class _IdGeneratorMock:
    def __init__(self) -> None:
        super().__init__()
        self.generated_ids = []
        self._next_id = 123

    def next_id(self):
        id = str(self._next_id)
        self._next_id += 1
        self.generated_ids.append(id)
        return id


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class MockAuthenticator(Authenticator):

    def __init__(self) -> None:
        super().__init__()
        self._users = {}

    def authenticate(self, request_handler):
        raise AuthRejectedError('Not implemented')

    def perform_basic_auth(self, user, password):
        if user not in self._users:
            raise AuthRejectedError('Invalid user ' + user)

        if self._users[user] != password:
            raise AuthRejectedError('Invalid password for user ' + user)

        return True

    def add_user(self, username, password):
        self._users[username] = password
