import logging
from string import Template

from ldap3 import Connection, SIMPLE

from auth import auth_base

KNOWN_REJECTIONS = [
    "invalidCredentials",
    "user name is mandatory in simple bind",
    "password is mandatory in simple bind"]


class LdapAuthorizer(auth_base.Authorizer):
    url = None
    username_template = None
    version = None

    def __init__(self, params_dict):
        self.url = params_dict.get("url")
        if not self.url:
            raise Exception("Url is compulsory parameter for LDAP auth")

        if params_dict.get("username_pattern"):
            self.username_template = Template(params_dict.get("username_pattern"))

        self.version = params_dict.get("version")
        if not self.version:
            self.version = 3

    def authenticate(self, username, password):
        logger = logging.getLogger("authorization")

        if self.username_template:
            user = self.username_template.substitute(username=username)
        else:
            user = username

        try:
            connection = Connection(
                self.url,
                user=user,
                password=password,
                authentication=SIMPLE,
                read_only=True,
                version=self.version
            )

            connection.bind()

            if connection.bound:
                connection.unbind()
                return True

            error = connection.last_error

        except Exception as e:
            error = str(e)

            if error not in KNOWN_REJECTIONS:
                logger.exception("Error occurred while ldap authentication")

        if error in KNOWN_REJECTIONS:
            raise auth_base.AuthRejectedError("Invalid credentials")

        raise auth_base.AuthFailureError(error)
