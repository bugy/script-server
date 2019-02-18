import logging
import os
from urllib.parse import urlparse

from tornado import httpclient

LOGGER = logging.getLogger('tornado_proxy_config')


def initialize():
    try:
        variable_names = ['HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy']
        for name in variable_names:
            proxy = os.environ.get(name)

            if proxy:
                try:
                    import pycurl
                except ImportError:
                    LOGGER.warning('System proxy is set, but requires python pycurl module. '
                                   'If you need a proxy, please install it')
                    return

                proxy_defaults = _read_proxy_defaults(proxy)
                httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient',
                                                     defaults=proxy_defaults)

                defaults_str = str({key: val if 'pass' not in key else '***' for key, val in proxy_defaults.items()})
                LOGGER.info('Configured global proxy: ' + defaults_str)
                return
    except:
        LOGGER.exception('Failed to read system proxy')


def _read_proxy_defaults(proxy):
    parsed = urlparse(proxy)

    defaults = {
        'proxy_host': parsed.hostname,
        'proxy_port': parsed.port}

    if not defaults['proxy_port']:
        defaults['proxy_port'] = 3128

    if parsed.username:
        defaults['proxy_username'] = parsed.username

    if parsed.password:
        defaults['proxy_password'] = parsed.password

    return defaults
