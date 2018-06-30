ANY_USER = 'ANY_USER'


class Authorizer:
    def __init__(self, app_allowed_users, admin_users):
        if ANY_USER in app_allowed_users:
            self._app_auth_check = AnyUserAuthorizationCheck()
        else:
            self._app_auth_check = ListBasedAuthorizationCheck(app_allowed_users)

        self._admin_users = admin_users

    def is_allowed_in_app(self, user_id):
        return self._app_auth_check.is_allowed(user_id)

    def is_admin(self, user_id):
        return user_id in self._admin_users


class ListBasedAuthorizationCheck:
    def __init__(self, allowed_users) -> None:
        self.allowed_users = allowed_users

    def is_allowed(self, user_id):
        return user_id in self.allowed_users


class AnyUserAuthorizationCheck:
    @staticmethod
    def is_allowed(user_id):
        return True
