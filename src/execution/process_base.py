import abc
import logging
import os
import signal
import subprocess
import threading

from react.observable import ReplayObservable
from utils import os_utils

LOGGER = logging.getLogger('script_server.process_base')

class ProcessWrapper(metaclass=abc.ABCMeta):
    def __init__(self, command, working_directory, env_variables):
        self.process = None

        self.working_directory = working_directory
        self.command = command
        self.env_variables = env_variables

        self.finish_listeners = []

        # output_stream is guaranteed to close not earlier than process exit
        self.output_stream = ReplayObservable()

        self.notify_finish_thread = None

    def start(self):
        self.start_execution(self.command, self.working_directory)

        read_output_thread = threading.Thread(target=self.pipe_process_output)
        read_output_thread.start()

        self.notify_finish_thread = threading.Thread(target=self.notify_finished)
        self.notify_finish_thread.start()

    def prepare_env_variables(self):
        env_variables = dict(os.environ, **self.env_variables)
        if 'PYTHONUNBUFFERED' not in env_variables:
            env_variables['PYTHONUNBUFFERED'] = '1'
        return env_variables

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

    def get_process_id(self):
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

            else:
                self.process.terminate()

            self._write_script_output('\n>> STOPPED BY USER\n')

    def kill(self):
        if not self.is_finished():
            if not os_utils.is_win():
                group_id = os.getpgid(self.get_process_id())
                os.killpg(group_id, signal.SIGKILL)
                self._write_script_output('\n>> KILLED\n')
            else:
                subprocess.Popen("taskkill /F /T /PID " + self.get_process_id())

    def add_finish_listener(self, listener):
        if self.is_finished():
            listener.finished()
            return

        self.finish_listeners.append(listener)

    def notify_finished(self):
        self.wait_finish()

        for listener in self.finish_listeners:
            try:
                listener.finished()
            except:
                LOGGER.exception('Failed to notify listener: ' + str(listener))

    def cleanup(self):
        self.output_stream.dispose()
