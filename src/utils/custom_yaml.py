import json
import re
import yaml

def loads (content, **args):
    contents=''
    for line in content.split('\n'):
        if not re.match (r'\s*//.*', line):
            contents += line + "\n"
    return yaml.safe_load(contents, **args)
