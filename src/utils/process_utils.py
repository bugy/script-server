import logging
import os
import shlex
import subprocess

from utils import file_utils
from utils import os_utils
from utils import string_utils
from utils.env_utils import EnvVariables

LOGGER = logging.getLogger('script_server.process_utils')


class ProcessInvoker:

    def __init__(self, env_vars: EnvVariables):
        super().__init__()
        self._env_vars = env_vars

    def invoke(self, command, work_dir='.', *, environment_variables: dict = None, check_stderr=True, shell=False):
        if isinstance(command, str) and not shell:
            command = split_command(command, working_directory=work_dir)

        env_vars = self._env_vars.build_env_vars(environment_variables)

        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd=work_dir,
                             env=env_vars,
                             universal_newlines=True,
                             shell=shell)

        (output, error) = p.communicate()

        result_code = p.returncode
        if result_code != 0:
            raise ExecutionException(result_code, error, output)

        if error and check_stderr:
            LOGGER.warning("Error output wasn't empty, although the command finished with code 0!")

        return output


def split_command(script_command, working_directory=None):
    if ' ' in script_command:
        if _is_file_path(script_command, working_directory):
            args = [script_command]
        else:
            posix = not os_utils.is_win()
            args = shlex.split(script_command, posix=posix)

            if not posix:
                args = [string_utils.unwrap_quotes(arg) for arg in args]
    else:
        args = [script_command]

    script_path = file_utils.normalize_path(args[0], working_directory)
    if (not os.path.isabs(script_path)) or (not os.path.exists(script_path)):
        script_path = args[0]

    script_args = args[1:]
    for i, body_arg in enumerate(script_args):
        expanded = os.path.expanduser(body_arg)
        if expanded != body_arg:
            script_args[i] = expanded

    return [script_path] + script_args


def _is_file_path(script_command_with_whitespaces, working_directory):
    if script_command_with_whitespaces.startswith('"') \
            or script_command_with_whitespaces.startswith("'"):
        return False

    file_exists = file_utils.exists(script_command_with_whitespaces, working_directory)
    if file_exists:
        LOGGER.warning('"%s" is a file with whitespaces'
                       ', please wrap it with quotes to avoid ambiguity',
                       script_command_with_whitespaces)
        return True

    return False


class ExecutionException(Exception):
    def __init__(self, exit_code, stderr, stdout):
        message = 'Execution failed. Code ' + str(exit_code)
        if stderr:
            message += ': ' + stderr
        elif stdout:
            last_line_start = stdout.rfind('\n')
            message += ': ' + stdout[last_line_start:]

        super().__init__(message)

        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
