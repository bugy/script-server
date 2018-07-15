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
    if ',dc=' in full_username:
        base_dn_start = full_username.find('dc=')
        return full_username[base_dn_start:]
    elif '@' in full_username:
        domain_start = full_username.find('@') + 1
        domain = full_username[domain_start:]
        domain_parts = domain.split('.')
        dcs = ('dc=' + name for name in domain_parts)
        return ','.join(dcs)
    else:
        return ''


class LdapAuthenticator(auth_base.Authenticator):
    def __init__(self, params_dict, temp_folder):
        super().__init__()

        self.url = model_helper.read_obligatory(params_dict, 'url', ' for LDAP auth')

        username_pattern = strip(params_dict.get('username_pattern'))
        if username_pattern:
            self.username_template = Template(username_pattern)
        else:
            self.username_template = None

        groups_base_dn = params_dict.get('groups_base_dn')
        if groups_base_dn:
            self._groups_base_dn = groups_base_dn.strip()
        else:
            resolved_base_dn = _resolve_base_dn(username_pattern)

            if resolved_base_dn:
                LOGGER.info('Resolved base dn for groups: ' + resolved_base_dn)
                self._groups_base_dn = resolved_base_dn
            else:
                LOGGER.warning(
                    'Cannot resolve LDAP base dn, so using empty. Please specify it using "groups_base_dn" attribute')
                self._groups_base_dn = ''

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
            connection = Connection(
                self.url,
                user=full_username,
                password=password,
                authentication=SIMPLE,
                read_only=True,
                version=self.version
            )

            connection.bind()

            if connection.bound:
                try:
                    user_groups = self._fetch_user_groups(username, full_username, connection)
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

    def get_groups(self, user):
        return self._get_groups(user)

    def _fetch_user_groups(self, username, full_username, connection):
        name_attribute = 'cn'
        base_dn = self._groups_base_dn

        search_filter = '(|(member=%s)(&(objectClass=posixGroup)(memberUid=%s)))' % (full_username, username)
        success = connection.search(base_dn, search_filter, attributes=[name_attribute])
        if not success:
            return []

        group_entries = connection.response
        if not group_entries:
            return []

        return [entry['attributes'][name_attribute][0] for entry in group_entries]

    def _load_groups(self, groups_file):
        if not os.path.exists(groups_file):
            return {}

        content = file_utils.read_file(groups_file)
        return json.loads(content)

    def _set_user_groups(self, user, groups):
        self._user_groups[user] = groups

        with open(self._groups_file, 'w') as fd:
            json.dump(self._user_groups, fd, indent=2)
