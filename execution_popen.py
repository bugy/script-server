import logging
import subprocess
import time

import execution


class POpenProcessWrapper(execution.ProcessWrapper):
    def __init__(self, command, command_identifier, working_directory, config):
        execution.ProcessWrapper.__init__(self, command, command_identifier, working_directory, config)

    def init_process(self, command, working_directory):
        self.process = subprocess.Popen(command,
                                        cwd=working_directory,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        start_new_session=True,
                                        universal_newlines=True)

    def write_to_input(self, value):
        input_value = value
        if not value.endswith("\n"):
            input_value += "\n"

        self.output.put(input_value)

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
                    self.output.put(output_text)

                if finished:
                    break

                if wait_new_output:
                    time.sleep(0.01)

        except:
            self.output.put("Unexpected error occurred. Contact the administrator.")

            logger = logging.getLogger("execution")
            try:
                self.kill()
            except:
                logger.exception("POpenProcessWrapper. Failed to kill a process")

            logger.exception("POpenProcessWrapper. Failed to read script output")
