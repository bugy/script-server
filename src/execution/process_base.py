import abc
import os
import signal
import subprocess
import threading

from react.observable import Observable
from utils import os_utils


class ProcessWrapper(metaclass=abc.ABCMeta):
    def __init__(self, command, working_directory):
        self.process = None

        self.working_directory = working_directory
        self.command = command

        self.finish_listeners = []

        self.output_stream = Observable()

    def start(self):
        self.start_execution(self.command, self.working_directory)

        read_output_thread = threading.Thread(target=self.pipe_process_output)
        read_output_thread.start()

        notify_finish_thread = threading.Thread(target=self.notify_finished)
        notify_finish_thread.start()

    @abc.abstractmethod
    def pipe_process_output(self):
        pass

    @abc.abstractmethod
    def start_execution(self, command, working_directory):
        pass

    @abc.abstractmethod
    def write_to_input(self, value):
        pass

    @abc.abstractmethod
    def wait_finish(self):
        pass

    def _get_process_id(self):
        return self.process.pid

    def is_finished(self):
        return self.process.poll() is not None

    def get_return_code(self):
        return self.process.returncode

    def _write_script_output(self, text):
        self.output_stream.push(text)

    def stop(self):
        if not self.is_finished():
            if not os_utils.is_win():
                group_id = os.getpgid(self._get_process_id())
                os.killpg(group_id, signal.SIGTERM)

                class KillChildren(object):
                    def finished(self):
                        try:
                            os.killpg(group_id, signal.SIGKILL)
                        except ProcessLookupError:
                            # probably there are no children left
                            pass

                self.add_finish_listener(KillChildren())

            else:
                self.process.terminate()

            self._write_script_output('\n>> STOPPED BY USER\n')

    def kill(self):
        if not self.is_finished():
            if not os_utils.is_win():
                group_id = os.getpgid(self._get_process_id())
                os.killpg(group_id, signal.SIGKILL)
                self._write_script_output('\n>> KILLED\n')
            else:
                subprocess.Popen("taskkill /F /T /PID " + self._get_process_id())

    def add_finish_listener(self, listener):
        self.finish_listeners.append(listener)

        if self.is_finished():
            self.notify_finished()

    def notify_finished(self):
        self.wait_finish()

        for listener in self.finish_listeners:
            listener.finished()
