import logging

import utils.env_utils as env_utils

ENV_VAR_PREFIX = '$$'
SECURE_MASK = '*' * 6

LOGGER = logging.getLogger('script_server.model_helper')


def resolve_env_var(value):
    if isinstance(value, str) and value.startswith(ENV_VAR_PREFIX):
        return env_utils.read_variable(value[2:])

    return value


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


def read_bool(value):
    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise Exception('Invalid value, should be bool or string. value=' + repr(value))

    return value.lower() == 'true'


def is_empty(value):
    return (not value) and (value != 0) and (value is not False)


def prepare_multiselect_values(param_values, parameters):
    for param in parameters:
        if (param.type == 'multiselect') and (param.name in param_values):
            value = param_values[param.name]
            if isinstance(value, list):
                continue
            if not is_empty(value):
                param_values[param.name] = [value]
            else:
                param_values[param.name] = []


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
