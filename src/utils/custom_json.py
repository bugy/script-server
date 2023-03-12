import json
import re

def loads (content, **args):
    contents=''
    for line in content.split('\n'):
        if not re.match (r'\s*//.*', line):
            contents += line + "\n"
    return json.loads(contents, **args)
