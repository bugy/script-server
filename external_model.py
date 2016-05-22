import json


class ExecutionInfo(object):
    script = None
    param_values = {}

    def set_script(self, value):
        self.script = value

    def get_script(self):
        return self.script

    def set_param_values(self, value):
        self.param_values = value

    def get_param_values(self):
        return self.param_values


def config_to_json(config):
    parameters = []
    for parameter in config.get_parameters():
        parameters.append({
            "name": parameter.get_name(),
            "description": parameter.get_description(),
            "withoutValue": parameter.is_no_value(),
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
    info.set_script(script)

    param_values = {}
    parameters = json_object.get("parameters")
    if parameters:
        for parameter in parameters:
            name = parameter.get("name")
            value = parameter.get("value")

            param_values[name] = value

    info.set_param_values(param_values)

    return info
