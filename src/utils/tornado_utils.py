import json
import re
from urllib import parse as urllib_parse
from urllib.parse import urljoin

from model.model_helper import is_empty


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

    for key in request_handler.request.arguments.keys():
        value = request_handler.get_argument(key, None)
        result[key] = value

    return result


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
