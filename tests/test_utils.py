import os
import shutil
import sys

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

    file_utils.write_file(os.path.join(folder, filename), 'test text')


def setup():
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)


def cleanup():
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    os_utils.sys_platform = sys.platform


def set_linux():
    os_utils.sys_platform = 'linux'


def set_win():
    os_utils.sys_platform = 'win'
