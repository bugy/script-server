import abc
import fcntl
import logging
import os
import pty
import queue
import signal
import subprocess
import sys
import threading
import time

script_encodings = {}


class ProcessWrapper(metaclass=abc.ABCMeta):
    process = None
    output = None
    command_identifier = None
    finish_listeners = []

    def __init__(self, command, command_identifier, working_directory):
        self.command_identifier = command_identifier

        self.init_process(command, working_directory)

        self.output = queue.Queue()

        read_output_thread = threading.Thread(target=self.pipe_process_output, args=())
        read_output_thread.start()

        notify_finish_thread = threading.Thread(target=self.notify_finished)
        notify_finish_thread.start()

    @abc.abstractmethod
    def pipe_process_output(self):
        pass

    @abc.abstractmethod
    def init_process(self, command, working_directory):
        pass

    @abc.abstractmethod
    def write_to_input(self, value):
        pass

    @abc.abstractmethod
    def wait_finish(self):
        pass

    def get_process_id(self):
        return self.process.pid

    def is_finished(self):
        return self.process.poll() is not None

    def stop(self):
        if not self.is_finished():
            group_id = os.getpgid(self.get_process_id())
            os.killpg(group_id, signal.SIGTERM)

            class KillChildren(object):
                def finished(self):
                    try:
                        os.killpg(group_id, signal.SIGKILL)
                    except ProcessLookupError:
                        # probably there are no children left
                        pass

            self.add_finish_listener(KillChildren())

            self.output.put("\n>> STOPPED BY USER\n")

    def kill(self):
        if not self.is_finished():
            group_id = os.getpgid(self.get_process_id())
            os.killpg(group_id, signal.SIGKILL)
            self.output.put("\n>> KILLED\n")

    def read(self):
        while True:
            try:
                result = self.output.get(True, 0.2)
                try:
                    added_text = result
                    while added_text:
                        added_text = self.output.get_nowait()
                        result += added_text
                except queue.Empty:
                    pass

                return result
            except queue.Empty:
                if self.is_finished():
                    break

    def add_finish_listener(self, listener):
        self.finish_listeners.append(listener)

        if self.is_finished():
            self.notify_finished()

    def notify_finished(self):
        self.wait_finish()

        for listener in self.finish_listeners:
            listener.finished()

    def get_command_identifier(self):
        return self.command_identifier


class PtyProcessWrapper(ProcessWrapper):
    pty_master = None
    pty_slave = None
    encoding = None

    def __init__(self, command, command_identifier, working_directory):
        if command_identifier in script_encodings:
            self.encoding = script_encodings[command_identifier]
        else:
            self.encoding = sys.stdout.encoding

        ProcessWrapper.__init__(self, command, command_identifier, working_directory)

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


class POpenProcessWrapper(ProcessWrapper):
    def __init__(self, command, command_identifier, working_directory):
        ProcessWrapper.__init__(self, command, command_identifier, working_directory)

    def init_process(self, command, working_directory):
        self.process = subprocess.Popen(command,
                                        cwd=working_directory,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        close_fds=True,
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


def set_script_encoding(command_identifier, encoding):
    script_encodings[command_identifier] = encoding
