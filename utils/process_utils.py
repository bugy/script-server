import subprocess

import six


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
