import sys

sys_platform = sys.platform


def is_win():
    return sys_platform.startswith('win')


def is_linux():
    return sys_platform == "linux" or sys_platform == "linux2"
