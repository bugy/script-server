class ListBasedAuthorizer:
    def __init__(self, allowed_users) -> None:
        self.allowed_users = allowed_users

    def is_allowed(self, username):
        return username in self.allowed_users


class AnyUserAuthorizer:
    @staticmethod
    def is_allowed(username):
        return True
