import datetime
import os
import os.path
import pathlib
import stat
import time


def modification_date(file_path):
    time_string = time.ctime(os.path.getmtime(file_path))
    return datetime.datetime.strptime(time_string, "%a %b %d %H:%M:%S %Y")


def deletion_date(file_path):
    path = pathlib.Path(file_path)

    while not path.exists():
        path = pathlib.Path(path.parent)

        if is_root(str(path)):
            raise Exception("Couldn't find parent folder for the deleted file " + file_path)

    return modification_date(str(path))


def is_root(path):
    return os.path.dirname(path) == path


def normalize_path(path_string):
    path_string = os.path.expanduser(path_string)

    if os.path.isabs(path_string):
        return path_string

    path = pathlib.Path(path_string)

    if path.exists():
        path = path.resolve()

    return str(path)


def read_file(filename):
    path = normalize_path(filename)

    file_content = ""
    with open(path, "r") as f:
        file_content += f.read()

    return file_content


def write_file(filename, content):
    path = normalize_path(filename)

    prepare_folder(os.path.dirname(path))

    with open(path, "w") as file:
        file.write(content)


def prepare_folder(folder_path):
    path = normalize_path(folder_path)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(path)


def make_executable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)


def exists(filename):
    path = normalize_path(filename)
    return os.path.exists(path)


def last_modification(folder_paths):
    result = None

    for root_folder_path in folder_paths:
        file_date = modification_date(root_folder_path)
        if (result is None) or (result < file_date):
            result = file_date

        for root, subdirs, files in os.walk(root_folder_path):
            root_path = pathlib.Path(root)
            for file in files:
                file_path = str(root_path.joinpath(file))
                file_date = modification_date(file_path)
                if (result is None) or (result < file_date):
                    result = file_date

            for folder in subdirs:
                folder_path = str(root_path.joinpath(folder))
                folder_date = modification_date(folder_path)
                if (result is None) or (result < folder_date):
                    result = folder_date

    return result
