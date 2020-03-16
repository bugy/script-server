import base64
import hashlib

from utils.apr1 import hash_apr1


def md5_apr1(salt, text):
    return hash_apr1(salt, text)


def sha1(text):
    result = hashlib.sha1(text.encode('utf8'))
    return base64.b64encode(result.digest()).decode('utf8')
