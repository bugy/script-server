import os

import utils.os_utils as os_utils
from auth.authorization import ANY_USER
from config.script.list_values import ConstValuesProvider, ScriptValuesProvider, EmptyValuesProvider, \
    DependantScriptValuesProvider
from model.model_helper import unwrap_conf_value


class Config(object):

    def __init__(self):
        self.config_path = None
        self.script_command = None
        self.name = None
        self.description = None
        self.requires_terminal = None
        self.parameters = None
        self.working_directory = None
        self.bash_formatting = None
        self.output_files = None

        self.parameters = []
        self.output_files = []

    def get_config_path(self):
        return self.config_path

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

    def find_parameter(self, param_name):
        for parameter in self.parameters:
            if parameter.name == param_name:
                return parameter
        return None


class Parameter(object):
    def __init__(self):
        self.name = None
        self.param = None
        self.no_value = None
        self.description = None
        self.required = None
        self.default = None
        self.type = 'text'
        self.min = None
        self.max = None
        self.constant = False
        self.values_provider = None
        self.secure = False
        self.separator = ','
        self.multiple_arguments = False

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

    def get_values(self, parameter_values):
        if self.values_provider:
            return self.values_provider.get_values(parameter_values)
        return []

    def get_required_parameters(self):
        if self.values_provider:
            return self.values_provider.get_required_parameters()
        return []


def read_name(file_path, json_object):
    name = json_object.get('name')
    if not name:
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]

    return name


def from_json(file_path, json_object, pty_enabled_default=False):
    config = Config()

    config.name = read_name(file_path, json_object)

    config.script_command = json_object.get("script_path")
    config.description = json_object.get("description")
    config.working_directory = json_object.get("working_directory")

    config.requires_terminal = read_boolean("requires_terminal", json_object, pty_enabled_default)
    config.bash_formatting = read_boolean("bash_formatting", json_object, os_utils.is_linux() or os_utils.is_mac())

    config.allowed_users = json_object.get('allowed_users')
    if config.allowed_users is None:
        config.allowed_users = ANY_USER

    output_files = json_object.get("output_files")
    if output_files:
        config.output_files = output_files

    parameters_json = json_object.get("parameters")

    if parameters_json is not None:
        parameter_values = {}

        for parameter_json in parameters_json:
            parameter = Parameter()
            parameter.set_name(parameter_json.get('name'))
            parameter.set_param(parameter_json.get('param'))
            parameter.set_no_value(parameter_json.get('no_value'))
            parameter.set_description(parameter_json.get('description'))
            parameter.set_required(parameter_json.get('required'))
            parameter.set_default(parameter_json.get('default'))
            parameter.set_min(parameter_json.get('min'))
            parameter.set_max(parameter_json.get('max'))
            parameter.secure = read_boolean('secure', parameter_json)
            parameter.separator = parameter_json.get('separator', ',')
            parameter.multiple_arguments = read_boolean('multiple_arguments', parameter_json, default=False)

            parameter_values[parameter] = parameter_json.get('values')

            type = parameter_json.get('type')
            if type:
                parameter.type = type

            constant = parameter_json.get("constant")
            if constant is True:
                if not parameter.get_default():
                    raise Exception("Constant should have default value specified")
                parameter.set_constant(constant)

            config.add_parameter(parameter)

        for parameter in config.parameters:
            values = parameter_values.get(parameter)
            if values is None:
                continue

            values_provider = _create_values_provider(values, parameter, config.parameters)
            parameter.values_provider = values_provider

    return config


def _create_values_provider(values, parameter, parameters):
    if values:
        if isinstance(values, list):
            return ConstValuesProvider(values)

        elif 'script' in values:
            script = values['script']

            if '${' not in script:
                return ScriptValuesProvider(script)

            return DependantScriptValuesProvider(script, parameters)

        else:
            raise Exception('Unsupported "values" format for ' + parameter.name)
    else:
        return EmptyValuesProvider()


def read_boolean(name, json_object, default=None):
    value = json_object.get(name)
    if value is not None:
        if value is True:
            return True
        elif value is False:
            return False
        else:
            raise Exception('"' + name + '" parameter should be True or False')
    else:
        return default


def get_default(parameter: Parameter):
    default = parameter.get_default()
    if not default:
        return default

    return unwrap_conf_value(default)
