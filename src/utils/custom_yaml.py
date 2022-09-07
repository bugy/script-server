import re

def loads (content, **args):
    import yaml
    return yaml.safe_load(content, **args)
