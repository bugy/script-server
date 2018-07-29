import json
import logging
import os
from string import Template

from ldap3 import Connection, SIMPLE

from auth import auth_base
from model import model_helper
from utils import file_utils
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


def _search(dn, search_filter, attributes, connection):
    success = connection.search(dn, search_filter, attributes=attributes)
    if not success:
        if connection.last_error:
            LOGGER.warning('ldap search failed: ' + connection.last_error
                           + '. dn:' + dn + ', filter: ' + search_filter)
        return None

    return connection.entries


def _load_multiple_entries_values(dn, search_filter, attribute_name, connection):
    entries = _search(dn, search_filter, [attribute_name], connection)
    if entries is None:
        return []

    result = []
    for entry in entries:
        value = entry[attribute_name].value
        if value is not None:
            result.append(value)

    return result


class LdapAuthenticator(auth_base.Authenticator):
    def __init__(self, params_dict, temp_folder):
        super().__init__()

        self.url = model_helper.read_obligatory(params_dict, 'url', ' for LDAP auth')

        username_pattern = strip(params_dict.get('username_pattern'))
        if username_pattern:
            self.username_template = Template(username_pattern)
        else:
            self.username_template = None

        base_dn = params_dict.get('base_dn')
        if base_dn:
            self._base_dn = base_dn.strip()
        else:
            resolved_base_dn = _resolve_base_dn(username_pattern)

            if resolved_base_dn:
                LOGGER.info('Resolved base dn: ' + resolved_base_dn)
                self._base_dn = resolved_base_dn
            else:
                LOGGER.warning(
                    'Cannot resolve LDAP base dn, so using empty. Please specify it using "base_dn" attribute')
                self._base_dn = ''

        self.version = params_dict.get("version")
        if not self.version:
            self.version = 3

        self._groups_file = os.path.join(temp_folder, 'ldap_groups.json')
        self._user_groups = self._load_groups(self._groups_file)

    def authenticate(self, request_handler):
        username = request_handler.get_argument('username')
        password = request_handler.get_argument('password')

        LOGGER.info('Logging in user ' + username)

        if self.username_template:
            full_username = self.username_template.substitute(username=username)
        else:
            full_username = username

        try:
            connection = self._connect(full_username, password)

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

    def _connect(self, full_username, password):
        connection = Connection(
            self.url,
            user=full_username,
            password=password,
            authentication=SIMPLE,
            read_only=True,
            version=self.version
        )
        connection.bind()
        return connection

    def _get_groups(self, user):
        groups = self._user_groups.get(user)
        if groups is not None:
            return groups

        groups = []
        self._user_groups[user] = groups
        return groups

    def get_groups(self, user):
        return self._get_groups(user)

    def _fetch_user_groups(self, user_dn, user_uid, connection):
        base_dn = self._base_dn

        result = set()

        result.update(_load_multiple_entries_values(base_dn, '(member=%s)' % user_dn, 'cn', connection))

        if user_uid:
            result.update(_load_multiple_entries_values(
                base_dn,
                '(&(objectClass=posixGroup)(memberUid=%s))' % user_uid,
                'cn',
                connection))

        return sorted(list(result))

    def _get_user_ids(self, full_username, connection):
        base_dn = self._base_dn

        username_lower = full_username.lower()
        if ',dc=' in username_lower:
            base_dn = username_lower
            search_filter = '(objectClass=*)'
        elif '@' in full_username:
            search_filter = '(userPrincipalName=%s)' % full_username
        elif '\\' in full_username:
            username_index = full_username.rfind('\\') + 1
            username = full_username[username_index:]
            search_filter = '(sAMAccountName=%s)' % username
        else:
            LOGGER.warning('Unsupported username pattern for ' + full_username)
            return full_username, None

        entries = _search(base_dn, search_filter, ['uid'], connection)
        if not entries:
            return full_username, None

        if len(entries) > 1:
            LOGGER.warning('More than one user found by filter: ' + search_filter)
            return full_username, None

        entry = entries[0]
        return entry.entry_dn, entry.uid.value

    def _load_groups(self, groups_file):
        if not os.path.exists(groups_file):
            return {}

        content = file_utils.read_file(groups_file)
        return json.loads(content)

    def _set_user_groups(self, user, groups):
        self._user_groups[user] = groups

        new_groups_content = json.dumps(self._user_groups, indent=2)
        file_utils.write_file(self._groups_file, new_groups_content)
