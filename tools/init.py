#!/usr/bin/env python3

import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..', 'src'))

from utils import process_utils


def prepare_project(project_path, *, prod):
    print('Building web...')
    npm_mode = 'prod' if prod else 'dev'
    process_utils.invoke('npm run build:' + npm_mode, os.path.join(project_path, 'web-src'))
    print('Done')

    runners_conf = os.path.join(project_path, 'conf', 'runners')
    if not os.path.exists(runners_conf):
        os.makedirs(runners_conf)


if __name__ == "__main__":
    script_folder = sys.path[0]
    if script_folder:
        project_path = os.path.abspath(os.path.join(script_folder, '..'))
    else:
        project_path = ''

    prepare_project(project_path, prod=False)
