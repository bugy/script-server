import json
import os


class Config(object):
    config_path = None
    script_path = None
    name = None
    description = None
    requires_terminal = None
    parameters = None

    def __init__(self):
        self.parameters = []

    def get_config_path(self):
        return self.config_path

    def get_script_path(self):
        return self.script_path

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def is_requires_terminal(self):
        return self.requires_terminal

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def get_parameters(self):
        return self.parameters


class Parameter(object):
    name = None
    param = None
    no_value = None
    description = None

    def get_name(self):
        return self.name

    def get_param(self):
        return self.param

    def is_no_value(self):
        return self.no_value

    def get_description(self):
        return self.description

    def set_name(self, value):
        self.name = value

    def set_param(self, value):
        self.param = value

    def set_no_value(self, value):
        self.no_value = value

    def set_description(self, value):
        self.description = value


def from_json(file_path, json_string):
    json_object = json.loads(json_string)
    config = Config()

    config.file_path = file_path
    config.name = json_object.get("name")
    if not config.name:
        filename = os.path.basename(file_path)
        config.name = os.path.splitext(filename)[0]

    config.script_path = json_object.get("script_path")
    config.description = json_object.get("description")

    requires_terminal = json_object.get("requires_terminal")
    if requires_terminal is not None:
        if requires_terminal.lower() == "true":
            config.requires_terminal = True
        elif requires_terminal.lower() == "false":
            config.requires_terminal = False
        else:
            raise Exception("'requires_terminal' parameter should be True or False")
    else:
        config.requires_terminal = False

    parameters_json = json_object.get("parameters")

    if parameters_json is not None:
        for parameter_json in parameters_json:
            parameter = Parameter()
            parameter.set_name(parameter_json.get("name"))
            parameter.set_param(parameter_json.get("param"))
            parameter.set_no_value(parameter_json.get("no_value"))
            parameter.set_description(parameter_json.get("description"))

            config.add_parameter(parameter)

    return config
