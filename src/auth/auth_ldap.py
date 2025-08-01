import json
import logging
import os
from string import Template

from ldap3 import Connection, SIMPLE, Server
from ldap3.core.exceptions import LDAPAttributeError
from ldap3.utils.conv import escape_filter_chars

from auth import auth_base
from model import model_helper
from utils import file_utils, custom_json
from utils.string_utils import strip

KNOWN_REJECTIONS = [
    "invalidCredentials",
    "user name is mandatory in simple bind",
    "password is mandatory in simple bind"]

LOGGER = logging.getLogger('script_server.LdapAuthorizer')


def _resolve_base_dn(full_username):
    if not full_username:
        return ''

    username_lower = full_username.lower()
    if ',dc=' in username_lower:
        base_dn_start = username_lower.find('dc=')
        return username_lower[base_dn_start:]

    elif '@' in full_username:
        domain_start = full_username.find('@') + 1
        domain = full_username[domain_start:]
        domain_parts = domain.split('.')
        dcs = ('dc=' + name for name in domain_parts)
        return ','.join(dcs)
    else:
        return ''


def _ldap_search(dn, search_request, attributes, connection):
    search_string = search_request.as_search_string()

    success = connection.search(dn, search_string, attributes=attributes)
    if not success:
        if connection.last_error:
            LOGGER.warning('ldap search failed: ' + connection.last_error
                           + '. dn:' + dn + ', filter: ' + search_string)
        return None

    return connection.entries


def _load_multiple_entries_values(dn, search_request, attribute_name, connection):
    entries = _ldap_search(dn, search_request, [attribute_name], connection)
    if entries is None:
        return []

    result = []
    for entry in entries:
        value = entry[attribute_name].value
        if value is not None:
            result.append(value)

    return result


def get_entry_dn(entry):
    try:
        return entry.entry_dn
    except LDAPAttributeError:
        return entry._dn


class LdapAuthenticator(auth_base.Authenticator):
    def __init__(self, params_dict, temp_folder):
        super().__init__()

        self._ldap_connector = LdapConnector(
            model_helper.read_obligatory(params_dict, 'url', ' for LDAP auth'),
            params_dict.get('version')
        )

        self._ldap_user_resolver = LdapUserResolver(
            params_dict.get('ldap_user_resolver'),
            self._ldap_connector)

        base_dn = params_dict.get('base_dn')
        if base_dn:
            self._base_dn = base_dn.strip()
        else:
            self._base_dn = self._ldap_user_resolver.auto_resolve_base_dn()
            if not self._base_dn:
                LOGGER.warning(
                    'Cannot resolve LDAP base dn, so using empty. Please specify it using "base_dn" attribute')
                self._base_dn = ''

        self._groups_file = os.path.join(temp_folder, 'ldap_groups.json')
        self._user_groups = self._load_groups(self._groups_file)

    def authenticate(self, request_handler):
        username = request_handler.get_argument('username')
        password = request_handler.get_argument('password')

        return self._authenticate_internal(username, password)

    def perform_basic_auth(self, user, password):
        self._authenticate_internal(user, password)
        return True

    def _authenticate_internal(self, username, password):
        LOGGER.info('Logging in user ' + username)

        full_username = self._ldap_user_resolver.resolve_ldap_username(username, self._base_dn)

        try:
            connection = self._ldap_connector.connect(full_username, password)

            if connection.bound:
                try:
                    user_dn, user_uid = self._get_user_ids(full_username, connection)
                    LOGGER.debug('user ids: ' + str((user_dn, user_uid)))

                    user_groups = self._fetch_user_groups(user_dn, user_uid, connection)
                    LOGGER.info('Loaded groups for ' + username + ': ' + str(user_groups))
                    self._set_user_groups(username, user_groups)
                except:
                    LOGGER.exception('Failed to load groups for the user ' + username)

                connection.unbind()
                return username

            error = connection.last_error

        except Exception as e:
            error = str(e)

            if error not in KNOWN_REJECTIONS:
                LOGGER.exception('Error occurred while ldap authentication of user ' + username)

        if error in KNOWN_REJECTIONS:
            LOGGER.info('Invalid credentials for user ' + username)
            raise auth_base.AuthRejectedError('Invalid credentials')

        raise auth_base.AuthFailureError(error)

    def _get_groups(self, user):
        groups = self._user_groups.get(user)
        if groups is not None:
            return groups

        groups = []
        self._user_groups[user] = groups
        return groups

    def get_groups(self, user, known_groups=None):
        return self._get_groups(user)

    def _fetch_user_groups(self, user_dn, user_uid, connection):
        base_dn = self._base_dn

        result = set()

        result.update(
            _load_multiple_entries_values(base_dn, SearchRequest('(member=%s)', user_dn), 'cn', connection))

        if user_uid:
            result.update(_load_multiple_entries_values(
                base_dn,
                SearchRequest('(&(objectClass=posixGroup)(memberUid=%s))', user_uid),
                'cn',
                connection))

        return sorted(list(result))

    def _get_user_ids(self, full_username, connection):
        base_dn = self._base_dn

        username_lower = full_username.lower()
        if ',dc=' in username_lower:
            base_dn = username_lower
            search_request = SearchRequest('(objectClass=*)')
        elif '@' in full_username:
            search_request = SearchRequest('(userPrincipalName=%s)', full_username)
        elif '\\' in full_username:
            username_index = full_username.rfind('\\') + 1
            username = full_username[username_index:]
            search_request = SearchRequest('(sAMAccountName=%s)', username)
        else:
            LOGGER.warning('Unsupported username pattern for ' + full_username)
            return full_username, None

        entry = LdapConnector.find_user(base_dn, search_request, connection)

        return get_entry_dn(entry), entry.uid.value

    def _load_groups(self, groups_file):
        if not os.path.exists(groups_file):
            return {}

        content = file_utils.read_file(groups_file)
        return custom_json.loads(content)

    def _set_user_groups(self, user, groups):
        self._user_groups[user] = groups

        new_groups_content = json.dumps(self._user_groups, indent=2)
        file_utils.write_file(self._groups_file, new_groups_content)


class SearchRequest:
    def __init__(self, template, *variables) -> None:
        escaped_vars = [escape_filter_chars(var) for var in variables]
        self.search_string = template % tuple(escaped_vars)

    def as_search_string(self):
        return self.search_string

    def __str__(self) -> str:
        return self.as_search_string()


class LdapConnector:
    def __init__(self, url, version):
        self.url = url
        self.version = version
        if not self.version:
            self.version = 3

    def connect(self, full_username, password):
        server = Server(self.url, connect_timeout=10)
        connection = Connection(
            server,
            user=full_username,
            password=password,
            authentication=SIMPLE,
            read_only=True,
            version=self.version,
        )
        connection.bind()
        return connection

    @staticmethod
    def find_user(base_dn, search_request, connection, attributes=None):
        if attributes is None:
            attributes = ['uid']

        entries = _ldap_search(base_dn, search_request, attributes, connection)
        if not entries:
            return None

        if len(entries) > 1:
            LOGGER.warning('More than one user found by filter: ' + str(search_request))
            return None

        return entries[0]


class LdapUserResolver:
    def __init__(self, config, ldap_connector: LdapConnector) -> None:
        self.username_template = None
        self.username_pattern = None
        self.search_by_attribute = None
        self.admin_user = None
        self.admin_password = None
        self.ldap_connector = ldap_connector

        if config:
            username_pattern = strip(config.get('username_pattern'))
            search_by_attribute = strip(config.get('search_by_attribute'))

            # Validate that either username_pattern or search_by_attribute is specified
            if not username_pattern and not search_by_attribute:
                raise ValueError(
                    'Either username_pattern or search_by_attribute must be specified in ldap_user_resolver.')

            if username_pattern and search_by_attribute:
                raise ValueError(
                    'Cannot specify both username_pattern and search_by_attribute in ldap_user_resolver. Choose one method.')

            if username_pattern:
                self.username_template = Template(username_pattern)
                self.username_pattern = username_pattern

            if search_by_attribute:
                self.search_by_attribute = search_by_attribute
                self.admin_user = model_helper.read_obligatory(
                    config,
                    'admin_user',
                    ' for ldap_user_resolver with search_by_attribute'
                )
                self.admin_password = model_helper.read_obligatory(
                    config,
                    'admin_password',
                    ' for ldap_user_resolver with search_by_attribute'
                )

    def resolve_ldap_username(self, username, base_dn):
        if self.username_template:
            return self.username_template.substitute(username=username)
        elif self.search_by_attribute:
            resolved_dn = self._find_user_dn_by_attribute(username, base_dn)
            return resolved_dn
        else:
            return username

    def auto_resolve_base_dn(self):
        if self.username_pattern:
            resolved_base_dn = _resolve_base_dn(self.username_pattern)
            if resolved_base_dn:
                LOGGER.info('Resolved base dn: ' + resolved_base_dn)
            return resolved_base_dn

        if self.search_by_attribute:
            resolved_base_dn = _resolve_base_dn(self.admin_user)
            if not resolved_base_dn:
                raise Exception('"base_dn" is required for search_by_attribute user resolution')
            return resolved_base_dn

        return None

    def _find_user_dn_by_attribute(self, username, base_dn):
        admin_connection = self.ldap_connector.connect(self.admin_user, self.admin_password)

        try:
            if not admin_connection.bound:
                error_msg = f'Failed to bind with admin LDAP user: {admin_connection.last_error}'
                LOGGER.error(error_msg)
                raise auth_base.AuthFailureError(error_msg)

            search_request = SearchRequest(f'({self.search_by_attribute}=%s)', username)

            user = self.ldap_connector.find_user(base_dn, search_request, admin_connection)
            if user is None:
                raise auth_base.AuthRejectedError('Invalid credentials')

            return get_entry_dn(user)

        finally:
            admin_connection.unbind()
