import json
import os

import utils.process_utils as process_utils


class Config(object):
    config_path = None
    script_command = None
    name = None
    description = None
    requires_terminal = None
    parameters = None
    working_directory = None
    bash_formatting = None
    output_files = None

    def __init__(self):
        self.parameters = []
        self.output_files = []

    def get_config_path(self):
        return self.config_path

    def get_script_command(self):
        return self.script_command

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

    def get_working_directory(self):
        return self.working_directory

    def is_bash_formatting(self):
        return self.bash_formatting


class Parameter(object):
    name = None
    param = None
    no_value = None
    description = None
    required = None
    default = None
    type = "text"
    min = None
    max = None
    constant = False
    values = None

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

    def set_required(self, value):
        self.required = value

    def is_required(self):
        return self.required

    def set_default(self, value):
        self.default = value

    def get_default(self):
        return self.default

    def set_type(self, value):
        self.type = value

    def get_type(self):
        return self.type

    def set_min(self, value):
        self.min = value

    def get_min(self):
        return self.min

    def set_max(self, value):
        self.max = value

    def get_max(self):
        return self.max

    def set_constant(self, value):
        self.constant = value

    def is_constant(self):
        return self.constant

    def set_values(self, value):
        self.values = value

    def get_values(self):
        return self.values


def read_name(file_path, json_string):
    json_object = json.loads(json_string)

    name = json_object.get("name")
    if not name:
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]

    return name


def from_json(file_path, json_string, pty_enabled_default=False):
    json_object = json.loads(json_string)
    config = Config()

    config.name = read_name(file_path, json_string)

    config.script_command = json_object.get("script_path")
    config.description = json_object.get("description")
    config.working_directory = json_object.get("working_directory")

    config.requires_terminal = read_boolean("requires_terminal", json_object, pty_enabled_default)
    config.bash_formatting = read_boolean("bash_formatting", json_object, (os.name == 'posix') or (os.name == 'mac'))

    output_files = json_object.get("output_files")
    if output_files:
        config.output_files = output_files

    parameters_json = json_object.get("parameters")

    if parameters_json is not None:
        for parameter_json in parameters_json:
            parameter = Parameter()
            parameter.set_name(parameter_json.get("name"))
            parameter.set_param(parameter_json.get("param"))
            parameter.set_no_value(parameter_json.get("no_value"))
            parameter.set_description(parameter_json.get("description"))
            parameter.set_required(parameter_json.get("required"))
            parameter.set_default(parameter_json.get("default"))
            parameter.set_min(parameter_json.get("min"))
            parameter.set_max(parameter_json.get("max"))

            values = parameter_json.get("values")
            if values:
                if isinstance(values, list):
                    parameter.set_values(values)

                elif "script" in values:
                    script_output = process_utils.invoke(values["script"])
                    script_output = script_output.rstrip("\n")
                    derived_values = script_output.split("\n")
                    parameter.set_values(derived_values)

                else:
                    raise Exception("Unsupported values")

            type = parameter_json.get("type")
            if type:
                parameter.set_type(type)

            constant = parameter_json.get("constant")
            if constant == True:
                if not parameter.get_default():
                    raise Exception("Constant should have default value specified")
                parameter.set_constant(constant)

            config.add_parameter(parameter)

    return config


def read_boolean(name, json_object, default=None):
    value = json_object.get(name)
    if value is not None:
        if value == True:
            return True
        elif value == False:
            return False
        else:
            raise Exception('"' + name + '" parameter should be True or False')
    else:
        return default
