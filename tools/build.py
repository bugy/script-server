#!/usr/bin/env python3

import glob
import os
import shutil
import zipfile

import init
from utils import file_utils

BUILD_FOLDER = 'build'


class BuildInfo():
    def __init__(self):
        self.files = set()

    def include(self, path):
        matching_files = file_utils.search_glob(path, recursive=True)

        for file in matching_files:
            self.files.add(file)

    def exclude(self, path):
        matching_files = file_utils.search_glob(path, recursive=True)

        for excluded in matching_files:
            if excluded in self.files:
                self.files.remove(excluded)

            if os.path.isdir(excluded):
                files_to_remove = []

                for file in self.files:
                    common_path = os.path.commonprefix([excluded, file])

                    if common_path == excluded:
                        files_to_remove.append(file)

                for file_to_remove in files_to_remove:
                    self.files.remove(file_to_remove)

    def get_files(self):
        return self.files


init.prepare_project('', prod=True)

build_info = BuildInfo()
build_info.include('launcher.py')
build_info.include(os.path.join('src', '**', '*.py'))
build_info.include(os.path.join('conf', 'logging.json'))
build_info.include(os.path.join('web', '**'))
build_info.include(os.path.join('conf', 'runners'))
build_info.exclude(os.path.join('src', 'tests'))
build_info.exclude('tools')
build_info.exclude('samples')
build_info.exclude(BUILD_FOLDER)

if os.path.exists(BUILD_FOLDER):
    shutil.rmtree(BUILD_FOLDER)
os.mkdir(BUILD_FOLDER)

zip = zipfile.ZipFile(os.path.join(BUILD_FOLDER, 'script-server.zip'), 'w', zipfile.ZIP_DEFLATED)
for file in build_info.get_files():
    zip.write(file)
