import utils.env_utils as env_utils
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
