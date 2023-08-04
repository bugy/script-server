import re
from typing import Optional, Callable

import tornado.httpserver
import tornado.netutil
from tornado.web import Application


class MockResponse:
    def __init__(self, body):
        self.body = body

    def __call__(self, request_handler):
        if self.body:
            request_handler.write(self.body)


class MatchResult:

    def __init__(self) -> None:
        self.matches = True
        self.match_count = 0
        self.unmatched_fields = {}

    def add_match(self):
        self.match_count += 1

    def add_miss(self, field_name, expected_value, actual_value):
        self.matches = False
        self.unmatched_fields[field_name] = (expected_value, actual_value)

    def add_match_result(self, field_name, expected_value, actual_value, custom_matcher=None):
        if custom_matcher:
            matches = custom_matcher()
        else:
            matches = expected_value == actual_value

        if matches:
            self.add_match()
        else:
            self.add_miss(field_name, expected_value, actual_value)


class _MockHandler:

    def __init__(self,
                 method: str,
                 path_pattern: str,
                 response_handler: Callable[[tornado.web.RequestHandler], None] = None,
                 headers: Optional[dict] = None,
                 request_body: Optional[str] = None) -> None:
        self.method = method.upper()
        self.path_pattern = path_pattern
        self.response_handler = response_handler
        self.request_body = request_body
        self.headers = headers

    def match(self, request_handler) -> MatchResult:
        match_result = MatchResult()

        match_result.add_match_result('method', self.method, request_handler.request.method)
        match_result.add_match_result(
            'path',
            self.path_pattern,
            request_handler.request.uri,
            lambda: re.match(self.path_pattern, request_handler.request.uri)
        )

        if self.request_body:
            actual_body = request_handler.request.body
            if actual_body:
                actual_body = actual_body.decode('utf8')
            match_result.add_match_result(
                'body',
                self.request_body,
                actual_body)

        if self.headers:
            for header, value in self.headers.items():
                actual_value = request_handler.request.headers.get(header)
                match_result.add_match_result('Header:' + header, value, actual_value)

        return match_result

    def handle(self, request_handler):
        if self.response_handler:
            self.response_handler(request_handler)

    def matcher_info(self):
        result = {
            'method': self.method,
            'path_pattern': self.path_pattern}

        if self.request_body:
            result['request_body'] = self.request_body

        if self.headers:
            result['headers'] = self.headers

        return str(result)


class MockServer:
    def __init__(self) -> None:
        application = Application(handlers=[(r'/.*', MockRequestHandler)])

        sockets = tornado.netutil.bind_sockets(0, '127.0.0.1')
        self._port = sockets[0].getsockname()[:2][1]
        self.server = tornado.httpserver.HTTPServer(application)
        self.server.add_sockets(sockets)
        application.mock_server = self

        self.mock_handlers: list[_MockHandler] = []

    def get_host(self):
        return 'http://127.0.0.1:' + str(self._port)

    def handle_request(self, request_handler: tornado.web.RequestHandler):
        all_matches = []
        for mock_handler in self.mock_handlers:
            all_matches.append((mock_handler, mock_handler.match(request_handler)))

        sorted_matches = sorted(all_matches, key=lambda x: (x[1].matches, x[1].match_count), reverse=True)

        (most_suitable_handler, match_result) = sorted_matches[0]

        if match_result.matches:
            most_suitable_handler.handle(request_handler)
            return

        raise Exception('Cannot match request + ' + repr(request_handler.request) + '\n'
                        + 'Most suitable handler : ' + most_suitable_handler.matcher_info() + '\n'
                        + 'Unmatches fields: ' + str(match_result.unmatched_fields))

    def register_mock(
            self,
            method,
            path_pattern,
            request_body=None,
            headers=None,
            response_handler: Callable[[tornado.web.RequestHandler], None] = None,
            response: MockResponse = None,
    ):
        if response and response_handler:
            raise Exception('response and response_handler cannot be specified at the same time')

        if response:
            response_handler = response

        handler = _MockHandler(
            method,
            path_pattern,
            request_body=request_body,
            headers=headers,
            response_handler=response_handler)

        self.mock_handlers.append(handler)

        return handler

    def unregister_mock(self, mock_handler):
        self.mock_handlers.remove(mock_handler)

    def cleanup(self):
        self.mock_handlers.clear()


class MockRequestHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.application.mock_server.handle_request(self)

    def post(self, *args, **kwargs):
        self.application.mock_server.handle_request(self)
