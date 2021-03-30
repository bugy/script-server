import json
import re

def loads (content):
    contents=""
    for line in content.split('\n'):
        if not re.match (r'\s*//.*', line):
            contents += line + "\n"
    # while "/*" in contents:
    #     preComment, postComment = contents.split("/*", 1)
    #     contents = preComment + postComment.split("*/", 1)[1]
    return json.loads(contents)
