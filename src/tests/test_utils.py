import os
import shutil
import stat

import utils.file_utils as file_utils
import utils.os_utils as os_utils

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


class SimpleStoringObserver:
    def __init__(self):
        self.data = []
        self.closed = False

    def on_next(self, chunk):
        if not self.closed:
            self.data.append(chunk)

    def on_close(self):
        if self.closed:
            raise Exception('Already closed')

        self.closed = True
