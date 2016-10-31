import abc


class Authorizer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def authenticate(self, username, password):
        pass


class AuthRejectedError(Exception):
    """Credentials, provided by user, were rejected by the authentication mechanism (user is unknown to the server)"""
    message = None

    def __init__(self, message=None):
        self.message = message

    def get_message(self):
        return self.message


class AuthFailureError(Exception):
    """Server-side error, which shows, that authentication process failed because of some internal error.
    These kind of errors are not related to user credentials"""
    message = None

    def __init__(self, message=None):
        self.message = message

    def get_message(self):
        return self.message
