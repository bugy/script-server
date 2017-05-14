import os
import shlex
import subprocess

import six

from utils import file_utils
from utils import os_utils


def invoke(command, work_dir="."):
    if isinstance(command, six.string_types):
        command = command.split()

    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=work_dir)

    (output_bytes, error_bytes) = p.communicate()

    output = output_bytes.decode("utf-8")
    error = error_bytes.decode("utf-8")

    result_code = p.returncode
    if result_code != 0:
        message = "Execution failed with exit code " + str(result_code)
        six.print_(message)
        six.print_(output)

        if error:
            six.print_(" --- ERRORS ---:")
            six.print_(error)
        raise Exception(message)

    if error:
        six.print_("WARN! Error output wasn't empty, although the command finished with code 0!")

    return output


def split_command(script_command, working_directory=None):
    if ' ' in script_command:
        posix = not os_utils.is_win()
        args = shlex.split(script_command, posix=posix)
    else:
        args = [script_command]

    script_path = file_utils.normalize_path(args[0], working_directory)
    script_args = args[1:]
    for i, body_arg in enumerate(script_args):
        expanded = os.path.expanduser(body_arg)
        if expanded != body_arg:
            script_args[i] = expanded

    result = [script_path]
    result.extend(script_args)

    return result
