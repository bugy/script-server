import os

os_name = os.name
path_separator = os.path.sep


def is_win():
    global os_name
    return os_name == 'nt'


def is_linux():
    global os_name
    return os_name == 'posix'


def is_mac():
    global os_name
    return os_name == 'mac'


def path_sep():
    global path_separator
    return path_separator


def is_pty_supported():
    return is_linux()


# THIS SHOULD BE USED IN TESTS ONLY!
def reset_os():
    global os_name
    global path_separator

    os_name = os.name
    path_separator = os.path.sep


def set_win():
    global os_name
    global path_separator
    os_name = 'nt'
    path_separator = '\\'


def set_linux():
    global os_name
    global path_separator
    os_name = 'posix'
    path_separator = '/'


def set_mac():
    global os_name
    global path_separator
    os_name = 'mac'
    path_separator = '/'
