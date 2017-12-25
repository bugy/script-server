import os
import re
from html.parser import HTMLParser

from utils import file_utils


def get_import_paths(project_path):
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

    css_folder = os.path.join(web_folder, 'css')
    for file in os.listdir(css_folder):
        if not file.endswith('.css'):
            continue

        file_path = os.path.join(css_folder, file)

        fonts_paths = extract_font_urls_from_css(file_path)
        for path in fonts_paths:
            imports.add(os.path.join('css', path))

    lib_paths = []
    for import_path in imports:
        if '/libs/' in import_path:
            lib_path = import_path.replace('/', os.path.sep)
            lib_path = os.path.join(web_folder, lib_path)

            lib_paths.append(lib_path)

    return lib_paths


def extract_font_urls_from_css(css_file):
    content = file_utils.read_file(css_file)
    matches = re.findall('url\(/?((\w+/)*fonts/[^)]+)\)', content)
    result = []
    for match in matches:
        url = match[0]
        result.append(url)

    return result


def validate_web_imports_exist(project_path):
    import_paths = get_import_paths(project_path)

    for import_path in import_paths:
        if not os.path.exists(import_path):
            raise Exception(import_path + " doesn't exist, please run tools/init.py")
