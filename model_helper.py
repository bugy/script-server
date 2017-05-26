import logging

import utils.env_utils as env_utils
import utils.string_utils as string_utils
from script_configs import Parameter

ENV_VAR_PREFIX = '$$'


def get_default(parameter: Parameter):
    default = parameter.get_default()
    if not default:
        return default

    return unwrap_conf_value(default)


def unwrap_conf_value(value):
    if isinstance(value, str) and value.startswith(ENV_VAR_PREFIX):
        return env_utils.read_variable(value[2:])

    return value


def is_empty(value):
    return (not value) and (value != 0) and (value != False)


def validate_parameters(parameters, config):
    logger = logging.getLogger("scriptServer")

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
                logger.error('Parameter ' + name + ' is not specified')
                return False
            continue

        if parameter.is_no_value():
            if value not in ['true', True, 'false', False]:
                logger.error('Parameter ' + name + ' should be boolean, but has value ' + str(value))
                return False
            continue

        if parameter.get_type() == 'text':
            continue

        if parameter.get_type() == 'int':
            if not (isinstance(value, int) or (isinstance(value, str) and string_utils.is_integer(value))):
                logger.error('Parameter ' + name + ' should be integer, but has value ' + str(value))
                return False

            int_value = int(value)

            if (not is_empty(parameter.get_max())) and (int_value > int(parameter.get_max())):
                logger.error('Parameter ' + name + ' is greater than allowed value (' +
                             str(value) + ' > ' + str(parameter.get_max()) + ')')
                return False

            if (not is_empty(parameter.get_min())) and (int_value < int(parameter.get_min())):
                logger.error('Parameter ' + name + ' is lower than allowed value (' +
                             str(value) + ' < ' + str(parameter.get_min()) + ')')
                return False

            continue

        if parameter.get_type() == 'list':
            if value not in parameter.get_values():
                logger.error('Parameter ' + name + ' has value ' + str(value) +
                             ', but should be in [' + ','.join(parameter.get_values()) + ']')
                return False
            continue

    return True
