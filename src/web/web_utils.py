import json
from itertools import chain

from auth.user import User
from utils import audit_utils


def wrap_to_server_event(event_type, data):
    return json.dumps({
        'event': event_type,
        'data': data
    })


def identify_user(request_handler):
    user_id = request_handler.application.identification.identify(request_handler)

    if user_id is None:
        raise Exception('Could not identify user: ' + audit_utils.get_all_audit_names(request_handler))

    return user_id


def inject_user(func):
    def wrapper(self, *args, **kwargs):
        user = get_user(self)

        new_args = chain([user], args)
        return func(self, *new_args, **kwargs)

    return wrapper


def get_user(request_handler):
    user_id = identify_user(request_handler)
    audit_names = audit_utils.get_all_audit_names(request_handler)

    return User(user_id, audit_names)
