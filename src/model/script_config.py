import json
import logging
import os
import re
from collections import OrderedDict

from auth.authorization import ANY_USER
from config.exceptions import InvalidConfigException
from model import parameter_config
from model.model_helper import is_empty, fill_parameter_values, read_bool_from_config, InvalidValueException, \
    read_str_from_config, replace_auth_vars
from model.parameter_config import ParameterModel
from react.properties import ObservableList, ObservableDict, observable_fields, Property
from utils import file_utils
from utils.object_utils import merge_dicts

OUTPUT_FORMAT_TERMINAL = 'terminal'

OUTPUT_FORMATS = [OUTPUT_FORMAT_TERMINAL, 'html', 'html_iframe', 'text']

LOGGER = logging.getLogger('script_server.script_config')


class ShortConfig(object):
    def __init__(self):
        self.name = None
        self.allowed_users = []
        self.admin_users = []
        self.group = None


@observable_fields(
    'script_command',
    'description',
    'requires_terminal',
    'working_directory',
    'output_format',
    'output_files',
    'schedulable',
    '_included_config')
class ConfigModel:

    def __init__(self,
                 config_object,
                 path,
                 username,
                 audit_name,
                 pty_enabled_default=True):
        super().__init__()

        short_config = read_short(path, config_object)
        self.name = short_config.name
        self._pty_enabled_default = pty_enabled_default
        self._config_folder = os.path.dirname(path)

        self._username = username
        self._audit_name = audit_name
        self.schedulable = False

        self.parameters = ObservableList()
        self.parameter_values = ObservableDict()

        self._original_config = config_object
        self._included_config_path = _TemplateProperty(config_object.get('include'),
                                                       parameters=self.parameters,
                                                       values=self.parameter_values)
        self._included_config_prop.bind(self._included_config_path, self._path_to_json)

        self._reload_config()

        self.parameters.subscribe(self)

        self._init_parameters(username, audit_name)

        for parameter in self.parameters:
            self.parameter_values[parameter.name] = parameter.default

        self._reload_parameters({})

        self._included_config_prop.subscribe(lambda old, new: self._reload(old))

    def set_param_value(self, param_name, value):
        parameter = self.find_parameter(param_name)
        if parameter is None:
            LOGGER.warning('Parameter ' + param_name + ' does not exist in ' + self.name)
            return
        validation_error = parameter.validate_value(value, ignore_required=True)

        if validation_error is not None:
            self.parameter_values[param_name] = None
            raise InvalidValueException(param_name, validation_error)

        self.parameter_values[param_name] = value

    def set_all_param_values(self, param_values, skip_invalid_parameters=False):
        original_values = dict(self.parameter_values)
        processed = {}

        anything_changed = True

        def get_sort_key(parameter):
            if parameter.name in self._included_config_path.required_parameters:
                return len(parameter.get_required_parameters())
            return 100 + len(parameter.get_required_parameters())

        sorted_parameters = sorted(self.parameters, key=get_sort_key)

        while (len(processed) < len(self.parameters)) and anything_changed:
            anything_changed = False

            parameters = sorted_parameters + [p for p in self.parameters if p not in sorted_parameters]
            for parameter in parameters:
                if parameter.name in processed:
                    continue

                required_parameters = parameter.get_required_parameters()
                if required_parameters and any(r not in processed for r in required_parameters):
                    continue

                value = parameter.normalize_user_value(param_values.get(parameter.name))
                validation_error = parameter.validate_value(value)
                if validation_error:
                    if skip_invalid_parameters:
                        logging.warning('Parameter ' + parameter.name + ' has invalid value, skipping')
                        value = parameter.normalize_user_value(None)
                    else:
                        self.parameter_values.set(original_values)
                        raise InvalidValueException(parameter.name, validation_error)

                self.parameter_values[parameter.name] = value
                processed[parameter.name] = parameter
                anything_changed = True

            if not anything_changed:
                remaining = [p.name for p in self.parameters if p.name not in processed]
                self.parameter_values.set(original_values)
                raise Exception('Could not resolve order for dependencies. Remaining: ' + str(remaining))

        for key, value in param_values.items():
            if self.find_parameter(key) is None:
                LOGGER.warning('Incoming value for unknown parameter ' + key)

    def list_files_for_param(self, parameter_name, path):
        parameter = self.find_parameter(parameter_name)
        if not parameter:
            raise ParameterNotFoundException(parameter_name)

        return parameter.list_files(path)

    def _init_parameters(self, username, audit_name):
        original_parameter_configs = self._original_config.get('parameters', [])
        for parameter_config in original_parameter_configs:
            parameter = ParameterModel(parameter_config, username, audit_name,
                                       lambda: self.parameters,
                                       self.parameter_values,
                                       self.working_directory)
            self.parameters.append(parameter)

        self._validate_parameter_configs()

    def _reload(self, old_included_config):
        self._reload_config()
        self._reload_parameters(old_included_config)

    def _reload_config(self):
        if self._included_config is None:
            config = self._original_config
        else:
            config = merge_dicts(self._original_config, self._included_config, ignored_keys=['parameters'])

        self.script_command = config.get('script_path')
        self.description = replace_auth_vars(config.get('description'), self._username, self._audit_name)
        self.working_directory = config.get('working_directory')

        required_terminal = read_bool_from_config('requires_terminal', config, default=self._pty_enabled_default)
        self.requires_terminal = required_terminal

        self.output_format = read_output_format(config)

        self.output_files = config.get('output_files', [])

        if config.get('scheduling'):
            self.schedulable = read_bool_from_config('enabled', config.get('scheduling'), default=False)

        if not self.script_command:
            raise Exception('No script_path is specified for ' + self.name)

    def _reload_parameters(self, old_included_config):
        original_parameters_names = {p.get('name') for p in self._original_config.get('parameters', [])}

        if old_included_config and old_included_config.get('parameters'):
            old_included_param_names = {p.get('name') for p in old_included_config.get('parameters', [])}
            for param_name in old_included_param_names:
                if param_name in original_parameters_names:
                    continue

                parameter = self.find_parameter(param_name)
                self.parameters.remove(parameter)

        if self._included_config is not None:
            included_parameter_configs = self._included_config.get('parameters', [])
            for parameter_config in included_parameter_configs:
                parameter_name = parameter_config.get('name')
                parameter = self.find_parameter(parameter_name)
                if parameter is None:
                    parameter = ParameterModel(parameter_config, self._username, self._audit_name,
                                               lambda: self.parameters,
                                               self.parameter_values,
                                               self.working_directory)
                    self.parameters.append(parameter)

                    if parameter.name not in self.parameter_values:
                        self.parameter_values[parameter.name] = parameter.default
                    continue
                else:
                    LOGGER.warning('Parameter ' + parameter_name + ' exists in original and included file. '
                                   + 'This is now allowed! Included parameter is ignored')
                    continue

    def find_parameter(self, param_name):
        for parameter in self.parameters:
            if parameter.name == param_name:
                return parameter
        return None

    def on_add(self, parameter, index):
        if self.schedulable and parameter.secure:
            LOGGER.warning(
                'Disabling schedulable functionality, because parameter ' + parameter.str_name() + ' is secure')
            self.schedulable = False

    def on_remove(self, parameter):
        pass

    def _validate_parameter_configs(self):
        for parameter in self.parameters:
            parameter.validate_parameter_dependencies(self.parameters)

    def _path_to_json(self, path):
        if path is None:
            return None

        Z={"parameters":[]}

        # Check if its a string or a list, for backwards compatibility
        if type(path) == str:
            path=[path]

        t=Z['parameters']
        for p in path:
            p = file_utils.normalize_path(p, self._config_folder)
            # LOGGER.debug (f"Importing template {p}")
            if os.path.exists(p):
                try:
                    this_json = json.loads( ( file_utils.read_file(p) ) )
                    for i in this_json.get('parameters'):
                        t.append (i)
                except:
                    LOGGER.exception('Failed to load included file ' + p)
                    return None
            else:
                LOGGER.warning('Failed to load included file, path does not exist: ' + p)
                return None
        return Z


def _read_name(file_path, json_object):
    name = json_object.get('name')
    if not name:
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]

    return name.strip()


def read_short(file_path, json_object):
    config = ShortConfig()

    config.name = _read_name(file_path, json_object)
    config.allowed_users = json_object.get('allowed_users')
    config.admin_users = json_object.get('admin_users')
    config.group = read_str_from_config(json_object, 'group', blank_to_none=True)

    hidden = read_bool_from_config('hidden', json_object, default=False)
    if hidden:
        return None

    if config.allowed_users is None:
        config.allowed_users = ANY_USER
    elif (config.allowed_users == '*') or ('*' in config.allowed_users):
        config.allowed_users = ANY_USER

    if config.admin_users is None:
        config.admin_users = ANY_USER
    elif (config.admin_users == '*') or ('*' in config.admin_users):
        config.admin_users = ANY_USER

    return config


class ParameterNotFoundException(Exception):
    def __init__(self, param_name) -> None:
        self.param_name = param_name


class _TemplateProperty:
    def __init__(self, template, parameters: ObservableList, values: ObservableDict, empty=None) -> None:
        self._value_property = Property(None)
        self._template = template
        self._values = values
        self._empty = empty
        self._parameters = parameters

        pattern = re.compile('\${([^}]+)\}')

        search_start = 0
        script_template = ''
        required_parameters = set()

        if template:
            # TODO: What is this doing? Counting the number of letter in the filename?
            while search_start < len(template):
                match = pattern.search(template, search_start)
                if not match:
                    script_template += template[search_start:]
                    break
                param_start = match.start()
                if param_start > search_start:
                    script_template += template[search_start:param_start]

                param_name = match.group(1)
                required_parameters.add(param_name)

                search_start = match.end() + 1

        self.required_parameters = tuple(required_parameters)

        self._reload()

        if self.required_parameters:
            values.subscribe(self._value_changed)
            parameters.subscribe(self)

    def _value_changed(self, parameter, old, new):
        if parameter in self.required_parameters:
            self._reload()

    def on_add(self, parameter, index):
        if parameter.name in self.required_parameters:
            self._reload()

    def on_remove(self, parameter):
        if parameter.name in self.required_parameters:
            self._reload()

    def _reload(self):
        values_filled = True
        for param_name in self.required_parameters:
            value = self._values.get(param_name)
            if is_empty(value):
                values_filled = False
                break

        if self._template is None:
            self.value = None
        elif values_filled:
            self.value = fill_parameter_values(self._parameters, self._template, self._values)
        else:
            self.value = self._empty

        self._value_property.set(self.value)

    def subscribe(self, observer):
        self._value_property.subscribe(observer)

    def unsubscribe(self, observer):
        self._value_property.unsubscribe(observer)

    def get(self):
        return self._value_property.get()


def get_sorted_config(config):
    key_order = ['name', 'script_path',
                 'working_directory',
                 'hidden',
                 'description',
                 'group',
                 'allowed_users',
                 'admin_users',
                 'schedulable',
                 'include',
                 'output_files',
                 'requires_terminal',
                 'output_format',
                 'parameters']

    def get_order(key):
        if key == 'parameters':
            return 99
        elif key in key_order:
            return key_order.index(key)
        else:
            return 50

    sorted_config = OrderedDict(sorted(config.items(), key=lambda item: get_order(item[0])))
    if config.get('parameters'):
        for i, param in enumerate(config['parameters']):
            config['parameters'][i] = parameter_config.get_sorted_config(param)

    return sorted_config


def read_output_format(config):
    output_format = config.get('output_format')
    if not output_format:
        output_format = OUTPUT_FORMAT_TERMINAL

    output_format = output_format.strip().lower()
    if output_format not in OUTPUT_FORMATS:
        raise InvalidConfigException('Invalid output format, should be one of: ' + str(OUTPUT_FORMATS))

    return output_format
