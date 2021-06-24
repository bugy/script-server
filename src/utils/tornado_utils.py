import json
import re
from urllib import parse as urllib_parse
from urllib.parse import urljoin

from model.model_helper import is_empty
from utils import string_utils
from utils.string_utils import unwrap_quotes


def respond_error(request_handler, status_code, message):
    request_handler.set_status(status_code)
    request_handler.write(message)


def redirect_relative(relative_url, request_handler, *args, **kwargs):
    full_url = get_full_url(relative_url, request_handler)
    redirect(full_url, request_handler, *args, **kwargs)


def is_ajax(request):
    requested_with = request.headers.get('X-Requested-With')
    return requested_with == 'XMLHttpRequest'


def redirect(full_url, request_handler, *args, **kwargs):
    if is_ajax(request_handler.request):
        # For AJAX we need custom handling because of:
        #   1. browsers ignore url fragments (#hash) of redirects inside ajax
        #   2. redirecting ajax to external resources causes allowed origin header issues
        request_handler.set_header('Location', full_url)
        request_handler.set_status(200)
    else:
        request_handler.redirect(full_url, *args, **kwargs)


def get_full_url(relative_url, request_handler):
    request = request_handler.request
    host_url = request.protocol + '://' + request.host
    return urljoin(host_url, relative_url)


def normalize_url(request_url):
    request_url_path = urllib_parse.urlparse(request_url).path
    normalized_path = re.sub('/{2,}', '/', request_url_path)
    normalized_path = re.sub('/+$', '', normalized_path)
    normalized_url = urllib_parse.urljoin(request_url, normalized_path)
    return normalized_url


def get_form_arguments(request_handler):
    result = {}

    arguments = request_handler.request.arguments
    for key, raw_value in arguments.items():
        if isinstance(raw_value, list) and (len(raw_value) > 1):
            value = request_handler.get_arguments(key)
        else:
            value = request_handler.get_argument(key, None)
        result[key] = value

    return result


def get_form_file(request_handler, argument_name):
    files = request_handler.request.files.get(argument_name)
    if files is None:
        return None
    return files[0]


def get_request_body(request_handler):
    raw_request_body = request_handler.request.body.decode('UTF-8')
    if is_empty(raw_request_body):
        return {}

    return json.loads(raw_request_body)


def get_proxied_ip(request_handler):
    forwarded_for = request_handler.request.headers.get('X-Forwarded-For', None)
    if forwarded_for:
        return forwarded_for

    return request_handler.request.headers.get('X-Real-IP', None)


def get_secure_cookie(request_handler, key):
    value = request_handler.get_secure_cookie(key)
    if value is None:
        return None

    return value.decode('utf-8')


def parse_header(header):
    header_split = []
    current = ''
    current_quote = None
    for char in header:
        if char == '"' or char == "'":
            if current_quote is None:
                current_quote = char
            elif current_quote == char:
                current_quote = None
        elif char == ';' and current_quote is None:
            if current:
                header_split.append(current)
            current = ''
            continue

        current += char

    if current:
        header_split.append(current)

    main_value = header_split[0]
    if ':' in main_value:
        main_value = main_value[main_value.index(':') + 1:]
    main_value = string_utils.unwrap_quotes(main_value.strip())

    sub_headers = header_split[1:]
    sub_headers_dict = {}
    for sub_header in sub_headers:
        split = sub_header.split('=', 1)

        if len(split) > 1:
            key = split[0].strip()
            value = unwrap_quotes(split[1].strip())
        else:
            key = sub_header.strip()
            value = ''

        sub_headers_dict[key] = value

    return main_value, sub_headers_dict
