import logging
import os
import subprocess
import time

from execution import process_base
from utils import os_utils

LOGGER = logging.getLogger('script_server.process_popen')


def prepare_cmd_for_win(command):
    shell = False

    command_path = command[0]
    if os.path.exists(command_path):
        file_extension = os.path.splitext(command_path)[1]
        if file_extension not in ['.bat', '.exe']:
            command = [command[0]] + [arg.replace('&', '^&') for arg in command[1:]]
            shell = True

    return command, shell


class POpenProcessWrapper(process_base.ProcessWrapper):
    def __init__(self, command, working_directory, env_variables):
        super().__init__(command, working_directory, env_variables)

    def start_execution(self, command, working_directory):
        shell = False

        if os_utils.is_win():
            (command, shell) = prepare_cmd_for_win(command)

        env_variables = self.prepare_env_variables()

        self.process = subprocess.Popen(command,
                                        cwd=working_directory,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        start_new_session=True,
                                        universal_newlines=True,
                                        shell=shell,
                                        env=env_variables)

    def write_to_input(self, value):
        input_value = value
        if not value.endswith("\n"):
            input_value += "\n"

        self._write_script_output(input_value)

        self.process.stdin.write(input_value)
        self.process.stdin.flush()

    def wait_finish(self):
        self.process.wait()

    def pipe_process_output(self):
        try:
            while True:
                finished = False
                wait_new_output = False

                if self.is_finished():
                    data = self.process.stdout.read()

                    finished = True

                else:
                    data = self.process.stdout.read(1)

                    if not data:
                        wait_new_output = True

                if data:
                    output_text = data
                    self._write_script_output(output_text)

                if finished:
                    break

                if wait_new_output:
                    time.sleep(0.01)

        except:
            self._write_script_output("Unexpected error occurred. Contact the administrator.")

            try:
                self.kill()
            except:
                LOGGER.exception('Failed to kill a process')

            LOGGER.exception('Failed to read script output')

        finally:
            self.output_stream.close()
