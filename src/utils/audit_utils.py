import base64
import logging
import socket
import sys

HOSTNAME = 'hostname'
IP = 'ip'
PROXIED_USERNAME = 'proxied_username'
AUTH_USERNAME = 'auth_username'

LOGGER = logging.getLogger('script_server.audit_utils')


def get_all_audit_names(request_handler):
    result = {}

    auth = request_handler.application.auth
    auth_username = auth.get_username(request_handler)
    if auth_username:
        result[AUTH_USERNAME] = auth_username

    basic_auth_username = find_basic_auth_username(request_handler)
    if basic_auth_username:
        result[PROXIED_USERNAME] = basic_auth_username

    remote_ip = request_handler.request.remote_ip
    result[IP] = remote_ip

    try:
        (hostname, aliases, ip_addresses) = socket.gethostbyaddr(remote_ip)
        result[HOSTNAME] = hostname
    except:
        LOGGER.warning("Couldn't get hostname for " + remote_ip)

    return result


def get_audit_name(all_audit_names):
    audit_types = [AUTH_USERNAME, PROXIED_USERNAME, HOSTNAME, IP]

    for name_type in audit_types:
        name = all_audit_names.get(name_type)

        if name:
            return name

    return None


def get_safe_username(all_audit_names):
    """
    Get the user credentials, which safely authorizes the user (either script-server auth username or IP)
    Safely means, that it's not easy for a fraud to imitate the name
    :param all_audit_names: 
    :return: user credentials (string)
    """
    if AUTH_USERNAME in all_audit_names:
        return all_audit_names[AUTH_USERNAME]
    else:
        return all_audit_names.get(IP)


def get_audit_name_from_request(request_handler):
    audit_names = get_all_audit_names(request_handler)

    return get_audit_name(audit_names)


def find_basic_auth_username(request_handler):
    auth_header = request_handler.request.headers.get('Authorization')
    if (auth_header is None) or (not auth_header.lower().startswith('basic ')):
        return None

    encoding = sys.getdefaultencoding()
    credential_bytes = base64.b64decode(auth_header[6:])
    credentials = credential_bytes.decode(encoding)
    username = credentials.split(':')[0]

    return username
