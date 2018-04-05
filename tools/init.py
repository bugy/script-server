#!/usr/bin/env python3

import os
import sys
import urllib.request

sys.path.insert(1, os.path.join(sys.path[0], '..', 'src'))

from utils import tool_utils

LIBRARIES = {
    'materialize.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.2/css/materialize.min.css',
    'jquery.min.js': 'https://code.jquery.com/jquery-2.1.1.min.js',
    'materialize.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.2/js/materialize.min.js',
    'hashtable.js': 'https://github.com/timdown/jshashtable/releases/download/v3.0/jshashtable-3.0.js',
    'MaterialIcons-Regular.woff2':
        'https://github.com/google/material-design-icons/blob/master/iconfont/MaterialIcons-Regular.woff2?raw=true',

    'vue.js': {
        'prod': 'https://cdnjs.cloudflare.com/ajax/libs/vue/2.5.15/vue.min.js',
        'dev': 'https://cdnjs.cloudflare.com/ajax/libs/vue/2.5.15/vue.js'
    },
    'vue-router.js': {
        'prod': 'https://cdnjs.cloudflare.com/ajax/libs/vue-router/3.0.1/vue-router.min.js',
        'dev': 'https://cdnjs.cloudflare.com/ajax/libs/vue-router/3.0.1/vue-router.js'
    }
}


def prepare_project(project_path, prod=True):
    import_paths = tool_utils.get_import_paths(project_path)

    for import_path in import_paths:
        library = os.path.basename(import_path)

        if library not in LIBRARIES:
            raise Exception(library + ' library URL is not specified')

        lib_parent_path = os.path.dirname(import_path)
        if not os.path.exists(lib_parent_path):
            os.makedirs(lib_parent_path)

        print('Downloading library ' + library + '...')
        url = LIBRARIES[library]
        if isinstance(url, dict):
            url = url['prod'] if prod else url['dev']

        urllib.request.urlretrieve(url, import_path)

    runners_conf = os.path.join(project_path, 'conf', 'runners')
    if not os.path.exists(runners_conf):
        os.makedirs(runners_conf)


if __name__ == "__main__":
    script_folder = sys.path[0]
    if script_folder:
        project_path = os.path.abspath(os.path.join(script_folder, '..'))
    else:
        project_path = ''

    prod = '--dev' not in sys.argv

    prepare_project(project_path, prod)
