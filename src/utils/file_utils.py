import datetime
import os
import os.path
import pathlib
import stat
import time

from utils import os_utils


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


def normalize_path(path_string, current_folder=None):
    path_string = os.path.expanduser(path_string)

    if os.path.isabs(path_string):
        return path_string

    if current_folder:
        path = pathlib.Path(normalize_path(current_folder))
        path = path.joinpath(path_string)
    else:
        path = pathlib.Path(path_string)

    if path.exists():
        return str(path.resolve())

    return path_string


def read_file(filename, byte_content=False):
    path = normalize_path(filename)

    mode = 'r'
    if byte_content:
        with open(path, mode + 'b') as f:
            return f.read()

    try:
        with open(path, mode) as f:
            return f.read()

    except UnicodeDecodeError as e:
        encoded_result = try_encoded_read(path)
        if encoded_result is not None:
            return encoded_result
        else:
            raise e


def try_encoded_read(path):
    encodings = ['utf_8', 'cp1251', 'iso-8859-1', 'koi8_r', 'cp1252', 'cp1250', 'latin1', 'utf_32']

    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            pass

    return None


def write_file(filename, content, byte_content=False):
    path = normalize_path(filename)

    prepare_folder(os.path.dirname(path))

    mode = "w"
    if byte_content:
        mode += "b"

    with open(path, mode) as file:
        file.write(content)


def prepare_folder(folder_path):
    path = normalize_path(folder_path)

    if not os.path.exists(path):
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


def relative_path(path, parent_path):
    path = normalize_path(path)
    parent_path = normalize_path(parent_path)

    if not path.startswith(parent_path):
        raise ValueError(path + ' is not subpath of ' + parent_path)

    relative_path = path[len(parent_path):]

    if relative_path.startswith(os.path.sep):
        return relative_path[1:]

    return relative_path


def split_all(path):
    result = []

    head = path
    while head and (not is_root(head)):
        (head, tail) = os.path.split(head)
        if tail:
            result.append(tail)

    result.reverse()
    return result


def to_filename(txt):
    if os_utils.is_win():
        return txt.replace(':', '-')

    return txt


def create_unique_filename(preferred_path, retries=9999999):
    original_filename = os.path.basename(preferred_path)
    folder = os.path.dirname(preferred_path)

    if not os.path.exists(preferred_path):
        return preferred_path

    i = 0

    filename_split = os.path.splitext(original_filename)
    extension = ''
    name = ''
    if len(filename_split) > 0:
        name = filename_split[0]
        if len(filename_split) > 1:
            extension = filename_split[1]

    while os.path.exists(preferred_path) and i < retries:
        preferred_path = os.path.join(folder, name + '_' + str(i) + extension)
        i += 1

    if os.path.exists(preferred_path):
        raise FileExistsException("Couldn't create unique filename for " + original_filename)

    return preferred_path


class FileExistsException(Exception):
    def __init__(self, *args) -> None:
        super().__init__(*args)
