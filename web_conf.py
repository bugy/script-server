import json
import os

import utils.file_utils as file_utils


class WebConfig(object):
    port = None
    ssl = False
    ssl_key_path = None
    ssl_cert_path = None
    authorizer = None

    def get_port(self):
        return self.port

    def is_ssl(self):
        return self.ssl

    def get_ssl_key_path(self):
        return self.ssl_key_path

    def get_ssl_cert_path(self):
        return self.ssl_cert_path

    def get_authorizer(self):
        return self.authorizer


def from_json(conf_path):
    if os.path.exists(conf_path):
        file_content = file_utils.read_file(conf_path)
    else:
        file_content = "{}"

    config = WebConfig()

    json_object = json.loads(file_content)

    port = 5000

    ssl = json_object.get("ssl")
    if ssl is not None:
        key_path = ssl.get("key_path")
        cert_path = ssl.get("cert_path")

        if not key_path:
            raise Exception("key_path is required for ssl")

        if not cert_path:
            raise Exception("cert_path is required for ssl")

        config.ssl = True
        config.ssl_key_path = key_path
        config.ssl_cert_path = cert_path
        port = 5443

    if json_object.get("port"):
        port = json_object.get("port")
    config.port = port

    if json_object.get("auth"):
        auth_object = json_object.get("auth")
        auth_type = auth_object.get("type")

        if not auth_type:
            raise Exception("Auth type should be specified")

        auth_type = auth_type.strip().lower()
        if auth_type == "ldap":
            from auth.auth_ldap import LdapAuthorizer
            config.authorizer = LdapAuthorizer(auth_object)

        else:
            raise Exception(auth_type + " auth is not supported")

    return config
