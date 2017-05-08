import os


def read_variable(variable_name):
    result = os.environ[variable_name]
    if result is None:
        raise Exception('Environment variable ' + variable_name + ' is not set')

    return result
