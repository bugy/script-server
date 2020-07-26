import datetime
import glob
import os
import os.path
import pathlib
import re
import stat
import sys
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
    path_string = os.path.normpath(path_string)

    if os.path.isabs(path_string):
        return path_string

    if current_folder:
        normalized_folder = normalize_path(current_folder)
        return os.path.join(normalized_folder, path_string)

    if not os.path.exists(path_string):
        return path_string

    return str(pathlib.Path(path_string).resolve())


def read_file(filename, byte_content=False, keep_newlines=False):
    path = normalize_path(filename)

    mode = 'r'
    if byte_content:
        with open(path, mode + 'b') as f:
            return f.read()

    try:
        newline = '' if keep_newlines else None
        with open(path, mode, newline=newline) as f:
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


def exists(filename, current_folder=None):
    path = normalize_path(filename, current_folder)
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

    if os_utils.is_win():
        path = path.capitalize()
        parent_path = parent_path.capitalize()

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
        return re.sub('[<>:"/\\\\|?*]', '_', txt)

    return txt.replace('/', '_')


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


def search_glob(path_pattern, recursive=None):
    if sys.version_info >= (3, 5):
        return glob.glob(path_pattern, recursive=recursive)
    else:
        if not recursive:
            return glob.glob(path_pattern)
        else:
            return _pre_3_5_recursive_glob(path_pattern)


def _pre_3_5_recursive_glob(path_pattern, parent_path=None):
    if path_pattern.startswith('~'):
        path_pattern = os.path.expanduser(path_pattern)

    file_name_regex = '([\w.-]|(\\\ ))*'

    pattern_chunks = path_pattern.split(os_utils.path_sep())

    current_paths = []
    if parent_path is not None:
        current_paths.append(parent_path)
    elif os.path.isabs(path_pattern):
        root_path = os.path.abspath(os.sep)
        current_paths.append(root_path)
    else:
        current_paths.append('')

    for i, pattern_chunk in enumerate(pattern_chunks):
        new_paths = []
        for current_path in current_paths:
            if '*' not in pattern_chunk:
                new_path = os.path.join(current_path, pattern_chunk)
                if os.path.exists(new_path):
                    new_paths.append(new_path)
            elif '**' not in pattern_chunk:
                if os.path.exists(current_path) and os.path.isdir(current_path):
                    pattern_chunk = pattern_chunk.replace('*', file_name_regex)
                    for file in os.listdir(current_path):
                        if re.match(pattern_chunk, file):
                            new_path = os.path.join(current_path, file)
                            new_paths.append(new_path)
            else:
                all_paths = []

                next_path_pattern = os.path.sep.join(pattern_chunks[i + 1:])
                if next_path_pattern == '':
                    next_path_pattern = '*'
                    all_paths.append(current_path + os.path.sep)
                all_paths.extend(_pre_3_5_recursive_glob(next_path_pattern, current_path))

                remaining_pattern = os.path.sep.join(pattern_chunks[i:])
                if os.path.exists(current_path) and os.path.isdir(current_path):
                    for file in os.listdir(current_path):
                        file_path = os.path.join(current_path, file)
                        if os.path.isdir(file_path):
                            all_paths.extend(_pre_3_5_recursive_glob(remaining_pattern, file_path))

                for child_path in all_paths:
                    if child_path.endswith('/') and child_path[:-1] in all_paths:
                        continue
                    new_paths.append(child_path)

        current_paths = new_paths

        if '**' in pattern_chunk:
            break

    return current_paths
