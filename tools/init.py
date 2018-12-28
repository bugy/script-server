#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..', 'src'))

from utils import process_utils


def download_web_files(project_path):
    print('Downloading web files...')

    from io import BytesIO
    from zipfile import ZipFile
    from urllib.request import urlopen

    response = urlopen('https://github.com/bugy/script-server/releases/download/dev/script-server.zip')
    with ZipFile(BytesIO(response.read())) as zipfile:
        for file in zipfile.namelist():
            if file.startswith('web/'):
                zipfile.extract(file, project_path)

    print('Done')


def build_web_files(prod, project_path):
    print('Building web...')
    npm_mode = 'prod' if prod else 'dev'
    process_utils.invoke('npm run build:' + npm_mode, os.path.join(project_path, 'web-src'))
    print('Done')


def prepare_project(project_path, *, prod, download_web=False):
    if download_web:
        download_web_files(project_path)
    else:
        build_web_files(prod, project_path)

    runners_conf = os.path.join(project_path, 'conf', 'runners')
    if not os.path.exists(runners_conf):
        os.makedirs(runners_conf)


if __name__ == "__main__":
    script_folder = sys.path[0]
    if script_folder:
        project_path = os.path.abspath(os.path.join(script_folder, '..'))
    else:
        project_path = ''

    parser = argparse.ArgumentParser(description='Initializes source code repo to make it runnable')
    parser.add_argument('--no-npm', action='store_true', default=False)
    parser.add_argument('--dev', action='store_true', default=False)
    args = vars(parser.parse_args())

    prepare_project(project_path, prod=not args['dev'], download_web=args['no_npm'])
