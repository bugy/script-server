import os
import sys


class EnvVariables:

    def __init__(self, os_variables, *, extra_variables=None, hidden_variables=None) -> None:
        super().__init__()

        self._variables = dict()
        if os_variables:
            self._variables.update(os_variables)

        if extra_variables:
            self._variables.update(extra_variables)

        if hidden_variables:
            for hidden_var in hidden_variables:
                self._variables.pop(hidden_var, None)

    def build_env_vars(self, extra_variables=None):
        result = dict(self._variables)

        if extra_variables:
            result.update(extra_variables)

        return result


def read_variable(variable_name, *, fail_on_missing=True):
    value = os.environ.get(variable_name)
    if fail_on_missing and (value == '' or value is None):
        raise Exception('Environment variable ' + variable_name + ' is not set')

    return value


def is_min_version(version, system_version=None):
    if system_version is None:
        system_version = sys.version_info

    version_split = str(version).split('.')

    try:
        major_expected = int(version_split[0])
        minor_expected = int(version_split[1])
    except ValueError:
        print("Couldn't parse version: " + version)
        return False

    return (system_version[0] == major_expected) and (system_version[1] >= minor_expected)
