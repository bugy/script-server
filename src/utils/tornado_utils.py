import re
from urllib import parse as urllib_parse
from urllib.parse import urljoin


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
