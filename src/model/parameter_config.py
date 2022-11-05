import logging
import os
from collections import OrderedDict
from ipaddress import ip_address, IPv4Address, IPv6Address

from config.constants import PARAM_TYPE_SERVER_FILE, FILE_TYPE_FILE, PARAM_TYPE_MULTISELECT, FILE_TYPE_DIR, \
    PARAM_TYPE_EDITABLE_LIST
from config.script.list_values import ConstValuesProvider, ScriptValuesProvider, EmptyValuesProvider, \
    DependantScriptValuesProvider, NoneValuesProvider, FilesProvider
from model import model_helper
from model.model_helper import resolve_env_vars, replace_auth_vars, is_empty, SECURE_MASK, \
    normalize_extension, read_bool_from_config, InvalidValueException, read_str_from_config
from react.properties import ObservableDict, observable_fields
from utils import file_utils, string_utils
from utils.file_utils import FileMatcher
from utils.process_utils import ProcessInvoker
from utils.string_utils import strip

LOGGER = logging.getLogger('script_server.parameter_config')


@observable_fields(
    'param',
    'same_arg_param'
    'env_var',
    'no_value',
    'description',
    'required',
    'default',
    'type',
    'min',
    'max',
    'max_length',
    'constant',
    '_values_provider',
    'values',
    'secure',
    'separator',
    'multiselect_argument_type',
    'file_dir',  # path relative to working dir (for execution)
    '_list_files_dir',  # file_dir, relative to the server path (for listing files)
    'file_type',
    'file_extensions',
    'file_recursive')
class ParameterModel(object):
    def __init__(self, parameter_config, username, audit_name, other_params_supplier,
                 process_invoker: ProcessInvoker,
                 other_param_values: ObservableDict = None,
                 working_dir=None):
        self._username = username
        self._audit_name = audit_name
        self._parameters_supplier = other_params_supplier
        self._working_dir = working_dir
        self._process_invoker = process_invoker

        self.name = parameter_config.get('name')

        self._original_config = parameter_config
        self._parameter_values = other_param_values

        self._reload()

        if (other_param_values is not None) \
                and (self._values_provider is not None) \
                and self._values_provider.get_required_parameters():
            other_param_values.subscribe(self._param_values_observer)

    def _reload(self):
        config = self._original_config

        self.param = config.get('param')
        self.same_arg_param = read_bool_from_config('same_arg_param', config, default=False)
        self.env_var = config.get('env_var')
        self.no_value = read_bool_from_config('no_value', config, default=False)
        self.description = replace_auth_vars(config.get('description'), self._username, self._audit_name)
        self.required = read_bool_from_config('required', config, default=False)
        self.min = config.get('min')
        self.max = config.get('max')
        self.max_length = config.get('max_length')
        self.secure = read_bool_from_config('secure', config, default=False)
        self.separator = config.get('separator', ',')
        self.multiselect_argument_type = read_str_from_config(
            config,
            'multiselect_argument_type',
            default='single_argument',
            allowed_values=['single_argument', 'argument_per_value', 'repeat_param_value'])
        self.type = self._read_type(config)
        self.default = _resolve_default(
            config.get('default'),
            self._username,
            self._audit_name,
            self._working_dir,
            self.type,
            self._process_invoker)
        self.file_dir = _resolve_file_dir(config, 'file_dir')
        self._list_files_dir = _resolve_list_files_dir(self.file_dir, self._working_dir)
        self.file_extensions = _resolve_file_extensions(config, 'file_extensions')
        self.file_type = _resolve_parameter_file_type(config, 'file_type', self.file_extensions)
        self.file_recursive = read_bool_from_config('file_recursive', config, default=False)
        self.excluded_files_matcher = _resolve_excluded_files(config, 'excluded_files', self._list_files_dir)

        self.constant = read_bool_from_config('constant', config, default=False)

        self._validate_config()

        values_provider = self._create_values_provider(
            config.get('values'),
            self.type,
            self.constant)
        self._values_provider = values_provider
        self._reload_values()

    def _validate_config(self):
        param_log_name = self.str_name()

        if self.constant and not self.default:
            message = 'Constant should have default value specified'
            raise Exception('Failed to set parameter "' + param_log_name + '" to constant: ' + message)

        if self.type == PARAM_TYPE_SERVER_FILE:
            if not self.file_dir:
                raise Exception('Parameter ' + param_log_name + ' has missing config file_dir')

    def str_name(self):
        names = (name for name in (self.name, self.param, self.description) if name)
        return next(names, 'unknown')

    def validate_parameter_dependencies(self, all_parameters):
        required_parameters = self.get_required_parameters()
        if not required_parameters:
            return

        parameters_dict = {p.name: p for p in all_parameters}

        for parameter_name in required_parameters:
            if parameter_name not in parameters_dict:
                raise Exception('Missing parameter "' + parameter_name + '" for the script')
            parameter = parameters_dict[parameter_name]
            unsupported_type = None

            if parameter.constant:
                unsupported_type = 'constant'
            elif parameter.secure:
                unsupported_type = 'secure'
            elif parameter.no_value:
                unsupported_type = 'no_value'

            if unsupported_type:
                raise Exception(
                    'Unsupported parameter "' + parameter_name
                    + '" of type "' + unsupported_type
                    + '" in values.script! ')

    def _read_type(self, config):
        type = config.get('type', 'text')

        if type.lower() in ('ip', 'ip4', 'ip6', 'ipv4', 'ipv6'):
            type = type.lower().replace('v', '')

        return type

    def _param_values_observer(self, key, old_value, new_value):
        values_provider = self._values_provider
        if values_provider is None:
            return

        if key not in values_provider.get_required_parameters():
            return

        self._reload_values()

    def _reload_values(self):
        values_provider = self._values_provider
        if not values_provider:
            self.values = None
            return

        values = values_provider.get_values(self._parameter_values)
        self.values = values

    def _create_values_provider(self, values_config, type, constant):
        if constant:
            return NoneValuesProvider()

        if self._is_plain_server_file():
            return FilesProvider(self._list_files_dir, self.file_type, self.file_extensions,
                                 self.excluded_files_matcher)

        if (type != 'list') and (type != PARAM_TYPE_MULTISELECT) and (type != PARAM_TYPE_EDITABLE_LIST):
            return NoneValuesProvider()

        if is_empty(values_config):
            return EmptyValuesProvider()

        if isinstance(values_config, list):
            return ConstValuesProvider(values_config)

        elif 'script' in values_config:
            original_script = values_config['script']
            has_variables = ('${' in original_script)

            script = replace_auth_vars(original_script, self._username, self._audit_name)
            shell = read_bool_from_config('shell', values_config, default=not has_variables)

            if '${' not in script:
                return ScriptValuesProvider(script, shell, self._process_invoker)

            return DependantScriptValuesProvider(script, self._parameters_supplier, shell, self._process_invoker)

        else:
            message = 'Unsupported "values" format for ' + self.name
            raise Exception(message)

    def get_required_parameters(self):
        if not self._values_provider:
            return []

        return self._values_provider.get_required_parameters()

    def normalize_user_value(self, value):
        if self.type == PARAM_TYPE_MULTISELECT or self._is_recursive_server_file():
            if isinstance(value, list):
                return value
            if not is_empty(value):
                return [value]
            else:
                return []

        return value

    def value_to_str(self, value):
        if self.secure:
            return SECURE_MASK

        return str(value)

    def value_to_repr(self, value):
        if self.secure:
            return SECURE_MASK

        return repr(value)

    def get_secured_value(self, value):
        if (not self.secure) or (value is None) or self.no_value:
            return value

        if isinstance(value, list):
            return [self.value_to_str(e) for e in value]

        return self.value_to_str(value)

    def map_to_script(self, user_value):
        def map_single_value(user_value):
            if self._values_provider:
                return self._values_provider.map_value(user_value)
            return user_value

        if self.type == PARAM_TYPE_MULTISELECT:
            return [map_single_value(v) for v in user_value]

        elif self._is_recursive_server_file():
            if user_value:
                return os.path.join(self.file_dir, *user_value)
            else:
                return None
        elif self._is_plain_server_file():
            if not is_empty(user_value):
                return os.path.join(self.file_dir, user_value)
            else:
                return None

        return map_single_value(user_value)

    def to_script_args(self, script_value):
        if self.type == PARAM_TYPE_MULTISELECT:
            if self.multiselect_argument_type == 'single_argument':
                return self.separator.join(script_value)
            else:
                return script_value

        return script_value

    def validate_value(self, value, *, ignore_required=False):
        if self.constant:
            return None

        if is_empty(value):
            if self.required and not ignore_required:
                return 'is not specified'
            return None

        value_string = self.value_to_repr(value)

        if self.no_value:
            if isinstance(value, bool):
                return None
            if isinstance(value, str) and value.lower() in ['true', 'false']:
                return None
            return 'should be boolean, but has value ' + value_string

        if self.type == 'text' or self.type == 'multiline_text':
            if (not is_empty(self.max_length)) and (len(value) > int(self.max_length)):
                return 'is longer than allowed char length (' \
                       + str(len(value)) + ' > ' + str(self.max_length) + ')'
            return None

        if self.type == 'file_upload':
            if not os.path.exists(value):
                return 'Cannot find file ' + value
            return None

        if self.type == 'int':
            if not (isinstance(value, int) or (isinstance(value, str) and string_utils.is_integer(value))):
                return 'should be integer, but has value ' + value_string

            int_value = int(value)

            if (not is_empty(self.max)) and (int_value > int(self.max)):
                return 'is greater than allowed value (' \
                       + value_string + ' > ' + str(self.max) + ')'

            if (not is_empty(self.min)) and (int_value < int(self.min)):
                return 'is lower than allowed value (' \
                       + value_string + ' < ' + str(self.min) + ')'
            return None

        if self.type in ('ip', 'ip4', 'ip6'):
            try:
                address = ip_address(value.strip())
                if self.type == 'ip4':
                    if not isinstance(address, IPv4Address):
                        return value_string + ' is not an IPv4 address'
                elif self.type == 'ip6':
                    if not isinstance(address, IPv6Address):
                        return value_string + ' is not an IPv6 address'
            except ValueError:
                return 'wrong IP address ' + value_string

        allowed_values = self.values

        if (self.type == 'list') or (self._is_plain_server_file()):
            if value not in allowed_values:
                return 'has value ' + value_string \
                       + ', but should be in ' + repr(allowed_values)
            return None

        if self.type == PARAM_TYPE_MULTISELECT:
            if not isinstance(value, list):
                return 'should be a list, but was: ' + value_string + '(' + str(type(value)) + ')'
            for value_element in value:
                if value_element not in allowed_values:
                    element_str = self.value_to_repr(value_element)
                    return 'has value ' + element_str \
                           + ', but should be in ' + repr(allowed_values)
            return None

        if self._is_recursive_server_file():
            return self._validate_recursive_path(value, intermediate=False)

        return None

    def list_files(self, path):
        if not self._is_recursive_server_file():
            raise WrongParameterUsageException(self.name, 'Can list files only for recursive file parameters')

        validation_error = self._validate_recursive_path(path, intermediate=True)
        if validation_error:
            raise InvalidValueException(self.name, validation_error)

        full_path = self._build_list_file_path(path)

        result = []

        if is_empty(self.file_type) or self.file_type == FILE_TYPE_FILE:
            files = model_helper.list_files(full_path,
                                            file_type=FILE_TYPE_FILE,
                                            file_extensions=self.file_extensions,
                                            excluded_files_matcher=self.excluded_files_matcher)
            for file in files:
                result.append({'name': file, 'type': FILE_TYPE_FILE, 'readable': True})

        dirs = model_helper.list_files(full_path,
                                       file_type=FILE_TYPE_DIR,
                                       excluded_files_matcher=self.excluded_files_matcher)
        for dir in dirs:
            dir_path = os.path.join(full_path, dir)

            readable = os.access(dir_path, os.R_OK)
            result.append({'name': dir, 'type': FILE_TYPE_DIR, 'readable': readable})

        return result

    def _is_plain_server_file(self):
        return self.type == PARAM_TYPE_SERVER_FILE and not self.file_recursive

    def _is_recursive_server_file(self):
        return self.type == PARAM_TYPE_SERVER_FILE and self.file_recursive

    def _validate_recursive_path(self, path, intermediate):
        value_string = self.value_to_str(path)

        if not isinstance(path, list):
            return 'should be a list, but was: ' + value_string + '(' + str(type(path)) + ')'

        if ('.' in path) or ('..' in path):
            return 'Relative path references are not allowed'

        full_path = self._build_list_file_path(path)

        if self.excluded_files_matcher.has_match(full_path):
            return 'Path ' + value_string + ' is excluded'

        if not os.path.exists(full_path):
            return 'Path ' + value_string + ' does not exist'

        if intermediate:
            if not os.access(full_path, os.R_OK):
                return 'Path ' + value_string + ' not accessible'

            if not os.path.isdir(full_path):
                return 'Path ' + value_string + ' is not a directory'

        else:
            dir = path[:-1]
            file = path[-1]

            dir_path = self._build_list_file_path(dir)
            allowed_files = model_helper.list_files(dir_path,
                                                    file_type=self.file_type,
                                                    file_extensions=self.file_extensions,
                                                    excluded_files_matcher=self.excluded_files_matcher)
            if file not in allowed_files:
                return 'Path ' + value_string + ' is not allowed'

    def _build_list_file_path(self, child_path):
        return os.path.normpath(os.path.join(self._list_files_dir, *child_path))


def _resolve_default(default, username, audit_name, working_dir, type, process_invoker: ProcessInvoker):
    if not default:
        return default

    script = False
    if isinstance(default, dict) and 'script' in default:
        string_value = default['script']
        script = True
    elif isinstance(default, str):
        string_value = default
    else:
        return default

    resolved_string_value = resolve_env_vars(string_value, full_match=True)
    if resolved_string_value == string_value:
        resolved_string_value = replace_auth_vars(string_value, username, audit_name)

    if script:
        has_variables = string_value != resolved_string_value
        shell = read_bool_from_config('shell', default, default=not has_variables)
        output = process_invoker.invoke(resolved_string_value, working_dir, shell=shell)
        stripped_output = output.strip()

        if type == PARAM_TYPE_MULTISELECT and '\n' in stripped_output:
            return [line.strip() for line in stripped_output.split('\n') if not is_empty(line)]

        return stripped_output

    return resolved_string_value


def _resolve_file_dir(config, key):
    raw_value = config.get(key)
    if not raw_value:
        return raw_value

    return resolve_env_vars(raw_value)


def _resolve_list_files_dir(file_dir, working_dir):
    if not file_dir or not working_dir:
        return file_dir

    return file_utils.normalize_path(file_dir, working_dir)


def _resolve_file_extensions(config, key):
    result = model_helper.read_list(config, key)
    if result is None:
        return []

    return [normalize_extension(e) for e in strip(result)]


def _resolve_excluded_files(config, key, file_dir):
    raw_patterns = model_helper.read_list(config, key)
    if raw_patterns is None:
        patterns = []
    else:
        patterns = [resolve_env_vars(e) for e in strip(raw_patterns)]
    return FileMatcher(patterns, file_dir)


def _resolve_parameter_file_type(config, key, file_extensions):
    if file_extensions:
        return FILE_TYPE_FILE

    value = config.get(key)

    if is_empty(value):
        return value

    return value.strip().lower()


class WrongParameterUsageException(Exception):
    def __init__(self, param_name, error_message) -> None:
        super().__init__(error_message)
        self.param_name = param_name


def get_sorted_config(param_config):
    key_order = ['name', 'required',
                 'param',
                 'same_arg_param',
                 'type', 'no_value', 'default', 'constant', 'description',
                 'secure',
                 'values',
                 'min',
                 'max',
                 'multiselect_argument_type',
                 'separator',
                 'file_dir',
                 'file_recursive',
                 'file_type',
                 'file_extensions',
                 'excluded_files']

    def get_order(key):
        if key in key_order:
            return key_order.index(key)
        else:
            return 100

    sorted_config = OrderedDict(sorted(param_config.items(), key=lambda item: get_order(item[0])))
    return sorted_config
