import logging
import os

import utils.custom_json as custom_json
import utils.file_utils as file_utils
from auth.authorization import ANY_USER
from model import model_helper
from model.model_helper import read_list, read_int_from_config, read_bool_from_config, ENV_VAR_PREFIX
from model.trusted_ips import TrustedIpValidator
from utils.env_utils import EnvVariables
from utils.process_utils import ProcessInvoker
from utils.string_utils import strip

LOGGER = logging.getLogger('server_conf')

XSRF_PROTECTION_TOKEN = 'token'
XSRF_PROTECTION_HEADER = 'header'
XSRF_PROTECTION_DISABLED = 'disabled'


class ServerConfig(object):
    def __init__(self) -> None:
        self.address = None
        self.port = None
        self.ssl = False
        self.ssl_key_path = None
        self.ssl_cert_path = None
        self.authenticator = None
        self.allowed_users = None
        self.alerts_config = None
        self.logging_config = None
        self.admin_config = None
        self.title = None
        self.enable_script_titles = None
        self.ip_validator = TrustedIpValidator([])
        self.user_groups = None
        self.admin_users = []
        self.full_history_users = []
        self.code_editor_users = []
        self.max_request_size_mb = None
        self.callbacks_config = None
        self.user_header_name = None
        self.secret_storage_file = None
        self.xsrf_protection = None
        # noinspection PyTypeChecker
        self.env_vars: EnvVariables = None

    def get_port(self):
        return self.port

    def is_ssl(self):
        return self.ssl

    def get_ssl_key_path(self):
        return self.ssl_key_path

    def get_ssl_cert_path(self):
        return self.ssl_cert_path


class LoggingConfig:
    def __init__(self, filename_pattern=None, date_format=None) -> None:
        self.filename_pattern = filename_pattern
        self.date_format = date_format

    @classmethod
    def from_json(cls, json_config):
        config = LoggingConfig()

        if json_config:
            json_logging_config = json_config
            config.filename_pattern = json_logging_config.get('execution_file')
            config.date_format = json_logging_config.get('execution_date_format')

        return config


def _build_env_vars(json_object):
    sensitive_config_paths = [
        ['auth', 'secret'],
        ['alerts', 'destinations', 'password'],
        ['callbacks', 'destinations', 'password']
    ]

    sensitive_env_vars = []

    def check_and_add_value(value):
        if isinstance(value, str) and value.startswith(ENV_VAR_PREFIX):
            sensitive_env_vars.append(value[2:])

    for config_path in sensitive_config_paths:
        value = model_helper.read_nested(json_object, config_path)
        if value is None:
            continue

        if isinstance(value, str):
            check_and_add_value(value)

        if isinstance(value, list):
            for value_element in value:
                check_and_add_value(value_element)

    return EnvVariables(os.environ, hidden_variables=sensitive_env_vars)


def from_json(conf_path, temp_folder):
    if os.path.exists(conf_path):
        file_content = file_utils.read_file(conf_path)
    else:
        file_content = "{}"

    config = ServerConfig()

    json_object = custom_json.loads(file_content)

    address = "0.0.0.0"
    port = 5000

    ssl = json_object.get("ssl")
    if ssl is not None:
        key_path = model_helper.read_obligatory(ssl, 'key_path', ' for ssl')
        cert_path = model_helper.read_obligatory(ssl, 'cert_path', ' for ssl')

        config.ssl = True
        config.ssl_key_path = key_path
        config.ssl_cert_path = cert_path
        port = 5443

    if json_object.get("address"):
        address = json_object.get("address")
    config.address = address

    if json_object.get("port"):
        port = json_object.get("port")
    config.port = port

    if json_object.get('title'):
        config.title = json_object.get('title')
    config.enable_script_titles = read_bool_from_config('enable_script_titles', json_object, default=True)

    config.env_vars = _build_env_vars(json_object)

    access_config = json_object.get('access')
    if access_config:
        allowed_users = access_config.get('allowed_users')
        user_groups = model_helper.read_dict(access_config, 'groups')
        user_header_name = access_config.get('user_header_name')
    else:
        allowed_users = None
        user_groups = {}
        user_header_name = None

    auth_config = json_object.get('auth')
    if auth_config:
        config.authenticator = create_authenticator(
            auth_config,
            temp_folder,
            process_invoker=ProcessInvoker(config.env_vars))

        auth_type = config.authenticator.auth_type
        if auth_type == 'google_oauth' and allowed_users is None:
            raise Exception('access.allowed_users field is mandatory for ' + auth_type)

        def_trusted_ips = []
        def_admins = []
    else:
        def_trusted_ips = ['127.0.0.1', '::1']
        def_admins = def_trusted_ips

    if access_config:
        trusted_ips = strip(read_list(access_config, 'trusted_ips', default=def_trusted_ips))
        admin_users = _parse_admin_users(access_config, default_admins=def_admins)
        full_history_users = _parse_history_users(access_config)
        code_editor_users = _parse_code_editor_users(access_config, admin_users)
    else:
        trusted_ips = def_trusted_ips
        admin_users = def_admins
        full_history_users = []
        code_editor_users = def_admins

    security = model_helper.read_dict(json_object, 'security')

    config.allowed_users = _prepare_allowed_users(allowed_users, admin_users, user_groups)
    config.alerts_config = json_object.get('alerts')
    config.callbacks_config = json_object.get('callbacks')
    config.logging_config = LoggingConfig.from_json(json_object.get('logging'))
    config.user_groups = user_groups
    config.admin_users = admin_users
    config.full_history_users = full_history_users
    config.code_editor_users = code_editor_users
    config.user_header_name = user_header_name
    config.ip_validator = TrustedIpValidator(trusted_ips)

    config.max_request_size_mb = read_int_from_config('max_request_size', json_object, default=10)

    config.secret_storage_file = json_object.get('secret_storage_file', os.path.join(temp_folder, 'secret.dat'))
    config.xsrf_protection = _parse_xsrf_protection(security)

    return config


def create_authenticator(auth_object, temp_folder, process_invoker: ProcessInvoker):
    auth_type = auth_object.get('type')

    if not auth_type:
        raise Exception('Auth type should be specified')

    auth_type = auth_type.strip().lower()
    if auth_type == 'ldap':
        from auth.auth_ldap import LdapAuthenticator
        authenticator = LdapAuthenticator(auth_object, temp_folder)
    elif auth_type == 'google_oauth':
        from auth.auth_google_oauth import GoogleOauthAuthenticator
        authenticator = GoogleOauthAuthenticator(auth_object)
    elif auth_type == 'gitlab':
        from auth.auth_gitlab import GitlabOAuthAuthenticator
        authenticator = GitlabOAuthAuthenticator(auth_object)
    elif auth_type == 'htpasswd':
        from auth.auth_htpasswd import HtpasswdAuthenticator
        authenticator = HtpasswdAuthenticator(auth_object, process_invoker)
    else:
        raise Exception(auth_type + ' auth is not supported')

    authenticator.auth_expiration_days = float(auth_object.get('expiration_days', 30))

    authenticator.auth_type = auth_type

    return authenticator


def _prepare_allowed_users(allowed_users, admin_users, user_groups):
    if (allowed_users is None) or (allowed_users == '*'):
        return [ANY_USER]

    elif not isinstance(allowed_users, list):
        raise Exception('allowed_users should be list')

    coerced_users = strip(allowed_users)
    coerced_users = {user for user in coerced_users if len(user) > 0}

    if '*' in coerced_users:
        return [ANY_USER]

    if admin_users and (ANY_USER != admin_users) and (ANY_USER not in admin_users):
        coerced_users.update(admin_users)

    if user_groups:
        for group, users in user_groups.items():
            if (ANY_USER != users) and (ANY_USER not in users):
                coerced_users.update(users)

    return list(coerced_users)


def _parse_admin_users(json_object, default_admins=None):
    admins = strip(read_list(json_object, 'admin_users', default=default_admins))
    if '*' in admins:
        LOGGER.warning('Any user is allowed to access admin page, be careful!')
        return [ANY_USER]

    return admins


def _parse_history_users(json_object):
    full_history_users = strip(read_list(json_object, 'full_history', default=[]))
    if (isinstance(full_history_users, list) and '*' in full_history_users) \
            or full_history_users == '*':
        return [ANY_USER]

    return full_history_users


def _parse_code_editor_users(json_object, admin_users):
    full_code_editor_users = strip(read_list(json_object, 'code_editors', default=admin_users))
    if (isinstance(full_code_editor_users, list) and '*' in full_code_editor_users) \
            or full_code_editor_users == '*':
        return [ANY_USER]

    return full_code_editor_users


def _parse_xsrf_protection(security):
    return model_helper.read_str_from_config(security,
                                             'xsrf_protection',
                                             default=XSRF_PROTECTION_TOKEN,
                                             allowed_values=[XSRF_PROTECTION_TOKEN,
                                                             XSRF_PROTECTION_HEADER,
                                                             XSRF_PROTECTION_DISABLED])


class InvalidServerConfigException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
