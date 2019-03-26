import json
import logging
import os

import utils.file_utils as file_utils
from auth.authorization import ANY_USER
from model import model_helper
from model.model_helper import read_list, read_int_from_config
from utils.string_utils import strip

LOGGER = logging.getLogger('server_conf')

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
        self.trusted_ips = []
        self.user_groups = None
        self.admin_users = []
        self.max_request_size_mb = None

    def get_port(self):
        return self.port

    def is_ssl(self):
        return self.ssl

    def get_ssl_key_path(self):
        return self.ssl_key_path

    def get_ssl_cert_path(self):
        return self.ssl_cert_path

    def get_alerts_config(self):
        return self.alerts_config


class AlertsConfig:
    def __init__(self) -> None:
        self.destinations = []

    def add_destination(self, destination):
        self.destinations.append(destination)

    def get_destinations(self):
        return self.destinations


class LoggingConfig:
    def __init__(self) -> None:
        self.filename_pattern = None
        self.date_format = None


def from_json(conf_path, temp_folder):
    if os.path.exists(conf_path):
        file_content = file_utils.read_file(conf_path)
    else:
        file_content = "{}"

    config = ServerConfig()

    json_object = json.loads(file_content)

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

    access_config = json_object.get('access')
    if access_config:
        allowed_users = access_config.get('allowed_users')
        user_groups = model_helper.read_dict(access_config, 'groups')
    else:
        allowed_users = None
        user_groups = {}

    auth_config = json_object.get('auth')
    if auth_config:
        config.authenticator = create_authenticator(auth_config, temp_folder)

        auth_type = config.authenticator.auth_type
        if auth_type == 'google_oauth' and allowed_users is None:
            raise Exception('auth.allowed_users field is mandatory for ' + auth_type)

        def_trusted_ips = []
        def_admins = []
    else:
        def_trusted_ips = ['127.0.0.1', '::1']
        def_admins = def_trusted_ips

    if access_config:
        config.trusted_ips = strip(read_list(access_config, 'trusted_ips', default=def_trusted_ips))
        admin_users = _parse_admin_users(access_config, default_admins=def_admins)
    else:
        config.trusted_ips = def_trusted_ips
        admin_users = def_admins

    config.allowed_users = _prepare_allowed_users(allowed_users, admin_users, user_groups)
    config.alerts_config = parse_alerts_config(json_object)
    config.logging_config = parse_logging_config(json_object)
    config.user_groups = user_groups
    config.admin_users = admin_users

    config.max_request_size_mb = read_int_from_config('max_request_size', json_object, default=10)

    return config


def create_authenticator(auth_object, temp_folder):
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
    else:
        raise Exception(auth_type + ' auth is not supported')

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


def parse_alerts_config(json_object):
    if json_object.get('communications'):
        alerts_object = json_object.get('communications')
        destination_objects = alerts_object.get('destinations')

        if destination_objects:
            alerts_config = AlertsConfig()

            for destination_object in destination_objects:
                destination_type = destination_object.get('type')

                if destination_type == 'email':
                    import communications.destination_email as email
                    destination = email.EmailDestination(destination_object)
                elif destination_type == 'http':
                    import communications.destination_http as http
                    destination = http.HttpDestination(destination_object)
                else:
                    raise Exception('Unknown alert destination type: ' + destination_type)

                alerts_config.add_destination(destination)

            return alerts_config

    return None


def parse_logging_config(json_object):
    config = LoggingConfig()

    if json_object.get('logging'):
        json_logging_config = json_object.get('logging')
        config.filename_pattern = json_logging_config.get('execution_file')
        config.date_format = json_logging_config.get('execution_date_format')

    return config


def _parse_admin_users(json_object, default_admins=None):
    admins = strip(read_list(json_object, 'admin_users', default=default_admins))
    if '*' in admins:
        LOGGER.warning('Any user is allowed to access admin page, be careful!')
        return [ANY_USER]

    return admins
