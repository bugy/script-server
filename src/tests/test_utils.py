import os
import shutil
import stat
import threading
import time
import uuid

import utils.file_utils as file_utils
import utils.os_utils as os_utils
from execution.process_base import ProcessWrapper
from utils import audit_utils

temp_folder = 'tests_temp'


def create_file(filepath):
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    filename = os.path.basename(filepath)
    folder = os.path.join(temp_folder, os.path.dirname(filepath))
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, filename)
    file_utils.write_file(file_path, 'test text')

    return file_path


def setup():
    if os.path.exists(temp_folder):
        _rmtree()

    os.makedirs(temp_folder)


def cleanup():
    if os.path.exists(temp_folder):
        _rmtree()

    os_utils.reset_os()


def _rmtree():
    def on_rm_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)

    shutil.rmtree(temp_folder, onerror=on_rm_error)


def set_linux():
    os_utils.set_linux()


def set_win():
    os_utils.set_win()


def mock_object():
    return type('', (), {})()


def create_audit_names(ip=None, auth_username=None, proxy_username=None, hostname=None):
    result = {}
    if ip is not None:
        result[audit_utils.IP] = ip
    if auth_username is not None:
        result[audit_utils.AUTH_USERNAME] = auth_username
    if proxy_username is not None:
        result[audit_utils.PROXIED_USERNAME] = proxy_username
    if hostname is not None:
        result[audit_utils.HOSTNAME] = hostname
    return result


class _MockProcessWrapper(ProcessWrapper):
    def __init__(self, executor, command, working_directory):
        super().__init__(command, working_directory)

        self.exit_code = None
        self.finished = False
        self.process_id = int.from_bytes(uuid.uuid1().bytes, byteorder='big')
        self.finish_condition = threading.Condition()

    def _get_process_id(self):
        return self.process_id

    # method for tests
    def finish(self, exit_code):
        if self.is_finished():
            raise Exception('Cannot finish a script twice')
        self.__finish(exit_code)

    def stop(self):
        self.__finish(9)

    def kill(self):
        self.__finish(15)

    def __finish(self, exit_code):
        if self.finished:
            return

        with self.finish_condition:
            self.exit_code = exit_code
            self.finished = True
            self.output_stream.close()
            self.finish_condition.notify_all()

        self.notify_finish_thread.join()

    def is_finished(self):
        return self.finished

    def get_return_code(self):
        return self.exit_code

    def pipe_process_output(self):
        pass

    def start_execution(self, command, working_directory):
        pass

    def wait_finish(self):
        with self.finish_condition:
            while not self.finished:
                self.finish_condition.wait(0.01)

    def write_to_input(self, value):
        pass
