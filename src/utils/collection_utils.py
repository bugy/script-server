def get_first_existing(dict, *keys, default=None):
    for key in keys:
        if key in dict:
            return dict[key]

    return default


def put_multivalue(some_dict, key, value):
    """
    Puts a value in a dict. If key already exists, then value will be appended to existing value(s) as a list.
    Behavior is described by the following cases:
      - key not exists: just put value in dict
      - key has a single value: new list is created for [old_value,new_value] and stored into dict
      - key has multiple values: new_value is appended to the list
    :param dict: where to put new element
    :param key: co
    :param value: new value to add
    """
    if key not in some_dict:
        some_dict[key] = value
    elif isinstance(some_dict[key], list):
        some_dict[key].append(value)
    else:
        some_dict[key] = [some_dict[key], value]


def find_any(values, predicate):
    for value in values:
        if predicate(value):
            return value

    return None
