import types


def _start_request_decorator(func):
    def wrapper(self, *args, **kwargs):
        delegate = func(*args, **kwargs)

        _decorate(delegate, 'headers_received', _headers_received_decorator)

        return delegate

    return wrapper


def _headers_received_decorator(func):
    def wrapper(self, start_line, headers, *args, **kwargs):
        proto_header = headers.get('X-Scheme', headers.get('X-Forwarded-Proto'))

        if proto_header:
            # use only the last proto entry if there is more than one
            proto_header = proto_header.split(',')[-1].strip()
        if proto_header in ('http', 'https'):
            self.request_conn.context.protocol = proto_header

        return func(start_line, headers, *args, **kwargs)

    return wrapper


def _decorate(obj, method_name, decorator):
    original_method = getattr(obj, method_name)
    new_method = types.MethodType(decorator(original_method), obj)
    setattr(obj, method_name, new_method)


def autoapply_xheaders(application):
    _decorate(application, 'start_request', _start_request_decorator)
