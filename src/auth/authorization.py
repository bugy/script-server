ANY_USER = 'ANY_USER'


class Authorizer:
    def __init__(self, app_allowed_users, admin_users):
        if ANY_USER in app_allowed_users:
            self._app_auth_check = AnyUserAuthorizationCheck()
        else:
            self._app_auth_check = ListBasedAuthorizationCheck(app_allowed_users)

        self._admin_users = admin_users

    def is_allowed_in_app(self, username):
        return self._app_auth_check.is_allowed(username)

    def is_admin(self, username):
        return username in self._admin_users


class ListBasedAuthorizationCheck:
    def __init__(self, allowed_users) -> None:
        self.allowed_users = allowed_users

    def is_allowed(self, username):
        return username in self.allowed_users


class AnyUserAuthorizationCheck:
    @staticmethod
    def is_allowed(username):
        return True
