from utils import audit_utils
from utils.audit_utils import AUTH_USERNAME


class User:
    def __init__(self, user_id, audit_names):
        self.audit_names = audit_names
        self.user_id = user_id

    def get_audit_name(self):
        return audit_utils.get_audit_name(self.audit_names)

    def get_username(self):
        return self.audit_names.get(AUTH_USERNAME)

    def __str__(self) -> str:
        if AUTH_USERNAME in self.audit_names:
            return self.audit_names.get(AUTH_USERNAME)

        return str(self.audit_names)
