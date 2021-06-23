import json
import re

def loads (content):
    contents=''
    for line in content.split('\n'):
        if not re.match (r'\s*//.*', line):
            contents += line + "\n"
    return json.loads(contents)
