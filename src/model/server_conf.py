import json
import os

import utils.file_utils as file_utils
from auth.authorization import ANY_USER, Authorizer
from model import model_helper
from model.model_helper import read_list
from utils.string_utils import strip


class ServerConfig(object):
    def __init__(self) -> None:
        self.address = None
        self.port = None
        self.ssl = False
        self.ssl_key_path = None
        self.ssl_cert_path = None
        self.authenticator = None
        self.authorizer = None
        self.alerts_config = None
        self.admin_config = None
        self.title = None

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


def from_json(conf_path):
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

    auth_config = json_object.get('auth')
    admin_users = _parse_admin_users(json_object)
    if auth_config:
        config.authenticator = create_authenticator(auth_config)

        allowed_users = auth_config.get('allowed_users')

        auth_type = config.authenticator.auth_type
        if auth_type == 'google_oauth' and allowed_users is None:
            raise Exception('auth.allowed_users field is mandatory for ' + auth_type)

        config.authorizer = _create_authorizer(allowed_users, admin_users)
    else:
        config.authorizer = _create_authorizer('*', admin_users)

    config.alerts_config = parse_alerts_config(json_object)

    return config


def create_authenticator(auth_object):
    auth_type = auth_object.get('type')

    if not auth_type:
        raise Exception('Auth type should be specified')

    auth_type = auth_type.strip().lower()
    if auth_type == 'ldap':
        from auth.auth_ldap import LdapAuthenticator
        authenticator = LdapAuthenticator(auth_object)
    elif auth_type == 'google_oauth':
        from auth.auth_google_oauth import GoogleOauthAuthenticator
        authenticator = GoogleOauthAuthenticator(auth_object)
    else:
        raise Exception(auth_type + ' auth is not supported')

    authenticator.auth_type = auth_type

    return authenticator


def _create_authorizer(allowed_users, admin_users):
    if (allowed_users is None) or (allowed_users == '*'):
        coerced_users = [ANY_USER]

    elif not isinstance(allowed_users, list):
        raise Exception('allowed_users should be list')

    else:
        coerced_users = strip(allowed_users)
        coerced_users = [user for user in coerced_users if len(user) > 0]

        if '*' in coerced_users:
            coerced_users = [ANY_USER]

    return Authorizer(coerced_users, admin_users)


def parse_alerts_config(json_object):
    if json_object.get('alerts'):
        alerts_object = json_object.get('alerts')
        destination_objects = alerts_object.get('destinations')

        if destination_objects:
            alerts_config = AlertsConfig()

            for destination_object in destination_objects:
                destination_type = destination_object.get('type')

                if destination_type == 'email':
                    import alerts.destination_email as email
                    destination = email.EmailDestination(destination_object)
                elif destination_type == 'http':
                    import alerts.destination_http as http
                    destination = http.HttpDestination(destination_object)
                else:
                    raise Exception('Unknown alert destination type: ' + destination_type)

                alerts_config.add_destination(destination)

            return alerts_config

    return None


def _parse_admin_users(json_object):
    default_admins = ['127.0.0.1', 'localhost', 'ip6-localhost']
    admin_users = read_list(json_object, 'admin_users', default_admins)

    return strip(admin_users)
