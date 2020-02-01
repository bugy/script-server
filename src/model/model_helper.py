import logging
import os
import re

import utils.env_utils as env_utils
from config.constants import FILE_TYPE_DIR, FILE_TYPE_FILE

ENV_VAR_PREFIX = '$$'
SECURE_MASK = '*' * 6

LOGGER = logging.getLogger('script_server.model_helper')


def resolve_env_vars(value, *, full_match=False):
    if not isinstance(value, str) or is_empty(value):
        return value

    if full_match:
        if value.startswith(ENV_VAR_PREFIX):
            return env_utils.read_variable(value[2:])
        return value

    def resolve_var(match):
        var_match = match.group()
        var_name = var_match[2:]
        resolved = env_utils.read_variable(var_name, fail_on_missing=False)
        if resolved is not None:
            return resolved
        return var_match

    pattern = re.escape(ENV_VAR_PREFIX) + '\w+'
    return re.sub(pattern, resolve_var, value)


def read_obligatory(values_dict, key, error_suffix=''):
    value = values_dict.get(key)
    if is_empty(value):
        raise Exception('"' + key + '" is required attribute' + error_suffix)

    return value


def read_list(values_dict, key, default=None):
    """
    Reads value from values_dict as a list
    
    If value is a list, then list is returned
    
    If value is missing, then default value is returned (or an empty list if not specified)
    
    If value is a dictionary, then error is raised
    
    Otherwise, a list of single element is returned as a value
    """

    value = values_dict.get(key)
    if value is None:
        if default is not None:
            return default
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        raise Exception('"' + key + '" has invalid type. List expected, got dictionary')

    return [value]


def read_dict(values_dict, key, default=None):
    """
    Reads value from values_dict as a dictionary

    If value is a dict, then dict is returned

    If value is missing, then default value is returned (or an empty dict if not specified)

    Otherwise an error is raised
    """

    value = values_dict.get(key)
    if value is None:
        if default is not None:
            return default
        return {}

    if isinstance(value, dict):
        return value

    raise Exception('"' + key + '" has invalid type. Dict expected')


def read_bool_from_config(key, config_obj, *, default=None):
    value = config_obj.get(key)
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() == 'true'

    raise Exception('"' + key + '" field should be true or false')


def read_bool(value):
    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise Exception('Invalid value, should be bool or string. value=' + repr(value))

    return value.lower() == 'true'


def read_int_from_config(key, config_obj, *, default=None):
    value = config_obj.get(key)
    if value is None:
        return default

    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.strip() == '':
            return default
        try:
            return int(value)
        except ValueError as e:
            raise InvalidValueException(key, 'Invalid %s value: integer expected, but was: %s' % (key, value)) from e

    raise InvalidValueTypeException('Invalid %s value: integer expected, but was: %s' % (key, repr(value)))


def is_empty(value):
    return (not value) and (value != 0) and (value is not False)


def fill_parameter_values(parameter_configs, template, values):
    result = template

    for parameter_config in parameter_configs:
        if parameter_config.secure or parameter_config.no_value:
            continue

        parameter_name = parameter_config.name
        value = values.get(parameter_name)

        if value is None:
            value = ''

        if not isinstance(value, str):
            value = str(value)

        result = result.replace('${' + parameter_name + '}', str(value))

    return result


def replace_auth_vars(text, username, audit_name):
    result = text

    if not username:
        username = ''
    if not audit_name:
        audit_name = ''

    result = result.replace('${auth.username}', str(username))
    result = result.replace('${auth.audit_name}', str(audit_name))

    return result


def normalize_extension(extension):
    return re.sub('^\.', '', extension).lower()


def list_files(dir, file_type=None, file_extensions=None):
    if not os.path.exists(dir) or not os.path.isdir(dir):
        raise InvalidFileException(dir, 'Directory not found')

    result = []

    if not is_empty(file_extensions):
        file_type = FILE_TYPE_FILE

    sorted_files = sorted(os.listdir(dir), key=lambda s: s.casefold())
    for file in sorted_files:
        file_path = os.path.join(dir, file)

        if file_type:
            if file_type == FILE_TYPE_DIR and not os.path.isdir(file_path):
                continue
            elif file_type == FILE_TYPE_FILE and not os.path.isfile(file_path):
                continue

        if file_extensions and not os.path.isdir(file_path):
            _, extension = os.path.splitext(file_path)
            if normalize_extension(extension) not in file_extensions:
                continue

        result.append(file)

    return result


class InvalidFileException(Exception):
    def __init__(self, path, message) -> None:
        super().__init__(message)
        self.path = path


class InvalidValueException(Exception):
    def __init__(self, param_name, validation_error) -> None:
        super().__init__(validation_error)
        self.param_name = param_name


class InvalidValueTypeException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class AccessProhibitedException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
