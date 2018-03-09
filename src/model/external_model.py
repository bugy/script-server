import json

from model import model_helper


class ExecutionInfo(object):
    def __init__(self):
        self.param_values = {}
        self.script = None


def config_to_json(config):
    parameters = []
    for parameter in config.get_parameters():
        if parameter.is_constant():
            continue

        parameters.append({
            "name": parameter.get_name(),
            "description": parameter.get_description(),
            "withoutValue": parameter.is_no_value(),
            "required": parameter.is_required(),
            "default": model_helper.get_default(parameter),
            "type": parameter.type,
            "min": parameter.get_min(),
            "max": parameter.get_max(),
            "values": parameter.get_values(),
            "secure": parameter.secure
        })

    return json.dumps({
        "name": config.get_name(),
        "description": config.get_description(),
        "parameters": parameters
    })


def to_execution_info(request_parameters):
    NAME_KEY = '__script_name'

    script_name = request_parameters.get(NAME_KEY)

    param_values = {}
    for name, value in request_parameters.items():
        if name == NAME_KEY:
            continue
        param_values[name] = value

    info = ExecutionInfo()
    info.script = script_name
    info.param_values = param_values

    return info
