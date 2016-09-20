import abc
import os
import queue
import signal
import threading


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
