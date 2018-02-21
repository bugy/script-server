import abc


class Authorizer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def authenticate(self, request_handler):
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


class AuthRedirectedException(Exception):
    """Server-side exception to forward authentication to another URL"""

    def __init__(self, redirect_url):
        self.redirect_url = redirect_url
