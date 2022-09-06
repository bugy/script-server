import re
import yaml

def loads (content, **args):
    return yaml.safe_load(content, **args)
