#!/usr/bin/env python3

import os
import sys
import urllib.request
from html.parser import HTMLParser

sys.path.append(os.getcwd())

import utils.file_utils as file_utils


def prepare_project(project_path):
    LIBRARIES = {
        'materialize.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.2/css/materialize.min.css',
        'jquery.min.js': 'https://code.jquery.com/jquery-2.1.1.min.js',
        'materialize.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.2/js/materialize.min.js',
        'hashtable.js': 'https://github.com/timdown/jshashtable/releases/download/v3.0/jshashtable-3.0.js'
    }

    imports = set()

    class HtmlImportSearcher(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'script':
                for attr in attrs:
                    if attr[0] == 'src':
                        imports.add(attr[1])

            if tag == 'link':
                for attr in attrs:
                    if attr[0] == 'href':
                        imports.add(attr[1])

    web_folder = os.path.join(project_path, 'web')
    for file in os.listdir(web_folder):
        if not file.endswith('.html'):
            continue

        file_path = os.path.join(web_folder, file)

        parser = HtmlImportSearcher()
        parser.feed(file_utils.read_file(file_path))

    lib_paths = []
    for import_path in imports:
        if '/libs/' in import_path:
            lib_path = import_path.replace('/', os.path.sep)
            lib_path = os.path.join(web_folder, lib_path)

            lib_paths.append(lib_path)

    for lib_path in lib_paths:
        library = os.path.basename(lib_path)

        if library not in LIBRARIES:
            raise Exception(library + ' library URL is not specified')

        lib_parent_path = os.path.dirname(lib_path)
        if not os.path.exists(lib_parent_path):
            os.makedirs(lib_parent_path)

        print('Downloading library ' + library + '...')
        url = LIBRARIES[library]
        urllib.request.urlretrieve(url, lib_path)

    runners_conf = os.path.join(project_path, 'conf', 'runners')
    if not os.path.exists(runners_conf):
        os.makedirs(runners_conf)


if __name__ == "__main__":
    script_folder = sys.path[0]
    if script_folder:
        project_path = os.path.abspath(os.path.join(script_folder, '..'))
    else:
        project_path = ''

    prepare_project(project_path)
