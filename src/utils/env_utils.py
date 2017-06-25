import os
import sys


def read_variable(variable_name):
    result = os.environ[variable_name]
    if result is None:
        raise Exception('Environment variable ' + variable_name + ' is not set')

    return result


def is_min_version(version, system_version=sys.version_info):
    version_split = str(version).split('.')

    try:
        major_expected = int(version_split[0])
        minor_expected = int(version_split[1])
    except ValueError:
        print("Couldn't parse version: " + version)
        return False

    return (system_version[0] == major_expected) and (system_version[1] >= minor_expected)
