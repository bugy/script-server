def update_dict(dict, extension_dict, *, override=False, ignored_keys=None):
    for key, value in extension_dict.items():
        if (not override) and (key in dict):
            continue

        if ignored_keys and (key in ignored_keys):
            continue

        dict[key] = value


def merge_dicts(*dicts, override=False, ignored_keys=None):
    result = {}

    for dict in dicts:
        update_dict(result, dict, override=override, ignored_keys=ignored_keys)

    return result
