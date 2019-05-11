import abc


class Authenticator(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._client_visible_config = {}
        self.auth_type = None

    @abc.abstractmethod
    def authenticate(self, request_handler):
        pass

    def get_client_visible_config(self):
        return self._client_visible_config

    def get_groups(self, user, known_groups=None):
        return []


class AuthRejectedError(Exception):
    """Credentials, provided by user, were rejected by the authentication mechanism (user is unknown to the server)"""

    def __init__(self, message=None):
        self.message = message

    def get_message(self):
        return self.message


class AuthFailureError(Exception):
    """Server-side error, which shows, that authentication process failed because of some internal error.
    These kind of errors are not related to user credentials"""

    def __init__(self, message=None):
        self.message = message

    def get_message(self):
        return self.message


class AuthBadRequestException(Exception):
    """Server-side exception, when the data provided by user has invalid format or some data is missing.
    Usually it means wrong behaviour on client-side"""

    def __init__(self, message=None):
        self.message = message

    def get_message(self):
        return self.message
