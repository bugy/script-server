import fcntl
import logging
import os
import pty
import subprocess
import sys
import time

import execution

script_encodings = {}


def set_script_encoding(command_identifier, encoding):
    script_encodings[command_identifier] = encoding


class PtyProcessWrapper(execution.ProcessWrapper):
    pty_master = None
    pty_slave = None
    encoding = None

    def __init__(self, command, command_identifier, working_directory):
        if command_identifier in script_encodings:
            self.encoding = script_encodings[command_identifier]
        else:
            self.encoding = sys.stdout.encoding

        execution.ProcessWrapper.__init__(self, command, command_identifier, working_directory)

    def init_process(self, command, working_directory):
        master, slave = pty.openpty()
        self.process = subprocess.Popen(command,
                                        cwd=working_directory,
                                        stdin=slave,
                                        stdout=slave,
                                        stderr=slave,
                                        start_new_session=True,
                                        close_fds=True)
        self.pty_slave = slave
        self.pty_master = master

        fcntl.fcntl(self.pty_master, fcntl.F_SETFL, os.O_NONBLOCK)

    def write_to_input(self, value):
        input_value = value
        if not input_value.endswith("\n"):
            input_value += "\n"

        os.write(self.pty_master, input_value.encode())

    def wait_finish(self):
        self.process.wait()

    def pipe_process_output(self):
        try:

            while True:
                finished = False
                wait_new_output = False

                max_read_bytes = 1024

                if self.is_finished():
                    data = b""
                    while True:
                        try:
                            chunk = os.read(self.pty_master, max_read_bytes)
                            data += chunk

                            if len(chunk) < max_read_bytes:
                                break
                        except BlockingIOError:
                            break

                    finished = True

                else:
                    data = ""
                    try:
                        data = os.read(self.pty_master, max_read_bytes)
                        if data.endswith(b"\r"):
                            data += os.read(self.pty_master, 1)

                        if data and (self.encoding.lower() == "utf-8"):

                            while data[len(data) - 1] >= 127:
                                next_byte = os.read(self.pty_master, 1)
                                if not next_byte:
                                    break

                                data += next_byte
                    except BlockingIOError:
                        if self.is_finished():
                            finished = True

                    if not data:
                        wait_new_output = True

                if data:
                    output_text = data.decode(self.encoding)
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
                logger.exception("PtyProcessWrapper. Failed to kill a process")

            logger.exception("PtyProcessWrapper. Failed to read script output")

        finally:
            os.close(self.pty_master)
            os.close(self.pty_slave)
