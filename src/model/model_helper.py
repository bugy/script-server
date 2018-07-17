import logging
import os

import utils.env_utils as env_utils
import utils.string_utils as string_utils
from model.script_configs import Parameter

ENV_VAR_PREFIX = '$$'
SECURE_MASK = '*' * 6

LOGGER = logging.getLogger('script_server.model_helper')


def get_default(parameter: Parameter):
    default = parameter.get_default()
    if not default:
        return default

    return unwrap_conf_value(default)


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


def validate_parameters(parameters, config):
    for parameter in config.get_parameters():
        if parameter.is_constant():
            continue

        name = parameter.get_name()

        if name in parameters:
            value = parameters[name]
        else:
            value = None

        if is_empty(value):
            if parameter.is_required():
                LOGGER.error('Parameter ' + name + ' is not specified')
                return False
            continue

        value_string = value_to_str(value, parameter)

        if parameter.is_no_value():
            if value not in ['true', True, 'false', False]:
                LOGGER.error('Parameter ' + name + ' should be boolean, but has value ' + value_string)
                return False
            continue

        if parameter.type == 'text':
            continue

        if parameter.type == 'file_upload':
            if not os.path.exists(value):
                LOGGER.error('Cannot find file ' + value)
                return False
            continue

        if parameter.type == 'int':
            if not (isinstance(value, int) or (isinstance(value, str) and string_utils.is_integer(value))):
                LOGGER.error('Parameter ' + name + ' should be integer, but has value ' + value_string)
                return False

            int_value = int(value)

            if (not is_empty(parameter.get_max())) and (int_value > int(parameter.get_max())):
                LOGGER.error('Parameter ' + name + ' is greater than allowed value (' +
                             value_string + ' > ' + str(parameter.get_max()) + ')')
                return False

            if (not is_empty(parameter.get_min())) and (int_value < int(parameter.get_min())):
                LOGGER.error('Parameter ' + name + ' is lower than allowed value (' +
                             value_string + ' < ' + str(parameter.get_min()) + ')')
                return False

            continue

        if parameter.type == 'list':
            if value not in parameter.get_values():
                LOGGER.error('Parameter ' + name + ' has value ' + value_string +
                             ', but should be in [' + ','.join(parameter.get_values()) + ']')
                return False
            continue

        if parameter.type == 'multiselect':
            if not isinstance(value, list):
                LOGGER.error(
                    'Parameter ' + name + ' should be a list, but was: ' + value_string + '(' + str(type(value)) + ')')
                return False
            for value_element in value:
                if value_element not in parameter.get_values():
                    element_str = value_to_str(value_element, parameter)
                    LOGGER.error('Parameter ' + name + ' has value ' + element_str +
                                 ', but should be in [' + ','.join(parameter.get_values()) + ']')
                    return False
            continue

    return True


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
