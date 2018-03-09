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

    return True


def value_to_str(value, parameter):
    if parameter.secure:
        return SECURE_MASK

    return str(value)
