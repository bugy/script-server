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
            "type": parameter.get_type(),
            "min": parameter.get_min(),
            "max": parameter.get_max(),
            "values": parameter.get_values()
        })

    return json.dumps({
        "name": config.get_name(),
        "description": config.get_description(),
        "parameters": parameters
    })


def to_execution_info(request_data):
    json_object = json.loads(request_data)

    script = json_object.get("script")

    info = ExecutionInfo()
    info.script = script

    param_values = {}
    parameters = json_object.get("parameters")
    if parameters:
        for parameter in parameters:
            name = parameter.get("name")
            value = parameter.get("value")

            param_values[name] = value

    info.param_values = param_values

    return info
