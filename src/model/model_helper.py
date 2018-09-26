import logging
import os

import utils.env_utils as env_utils
import utils.string_utils as string_utils

ENV_VAR_PREFIX = '$$'
SECURE_MASK = '*' * 6

LOGGER = logging.getLogger('script_server.model_helper')


def unwrap_conf_value(value):
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


def validate_parameters(parameter_values, config):
    for parameter in config.get_parameters():
        name = parameter.get_name()

        error = validate_parameter(parameter, parameter_values)
        if error is not None:
            LOGGER.error('Parameter ' + name + ': ' + error)
            return False

    return True


def validate_parameter(parameter, parameter_values):
    if parameter.is_constant():
        return None

    value = parameter_values.get(parameter.name)
    if is_empty(value):
        if parameter.is_required():
            return 'is not specified'
        return None

    value_string = value_to_str(value, parameter)

    if parameter.is_no_value():
        if value not in ['true', True, 'false', False]:
            return 'should be boolean, but has value ' + value_string
        return None

    if parameter.type == 'text':
        return None

    if parameter.type == 'file_upload':
        if not os.path.exists(value):
            return 'Cannot find file ' + value
        return None

    if parameter.type == 'int':
        if not (isinstance(value, int) or (isinstance(value, str) and string_utils.is_integer(value))):
            return 'should be integer, but has value ' + value_string

        int_value = int(value)

        if (not is_empty(parameter.get_max())) and (int_value > int(parameter.get_max())):
            return 'is greater than allowed value (' \
                   + value_string + ' > ' + str(parameter.get_max()) + ')'

        if (not is_empty(parameter.get_min())) and (int_value < int(parameter.get_min())):
            return 'is lower than allowed value (' \
                   + value_string + ' < ' + str(parameter.get_min()) + ')'
        return None

    allowed_values = parameter.get_values(parameter_values)

    if parameter.type == 'list':
        if value not in allowed_values:
            return 'has value ' + value_string \
                   + ', but should be in [' + ','.join(allowed_values) + ']'
        return None

    if parameter.type == 'multiselect':
        if not isinstance(value, list):
            return 'should be a list, but was: ' + value_string + '(' + str(type(value)) + ')'
        for value_element in value:
            if value_element not in allowed_values:
                element_str = value_to_str(value_element, parameter)
                return 'has value ' + element_str \
                       + ', but should be in [' + ','.join(allowed_values) + ']'
        return None

    return None


def value_to_str(value, parameter):
    if parameter.secure:
        return SECURE_MASK

    return str(value)


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
