def get_first_existing(dict, *keys, default=None):
    for key in keys:
        if key in dict:
            return dict[key]

    return default
