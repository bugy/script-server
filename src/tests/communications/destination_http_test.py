import json
import unittest

from communications.communication_model import File
from communications.destination_http import HttpDestination
from tests.communications.communication_test_utils import mock_communicators


@mock_communicators
class TestHttpDestination(unittest.TestCase):
    def test_send_simple_string(self):
        destination = HttpDestination({})
        destination.send('ignored', 'Hello world')

        self.assert_sent_data('Hello world')

    def test_send_dict(self):
        destination = HttpDestination({})
        body = {'p1': 5, 'test': True, 'some_str': 'abc'}
        destination.send('ignored', body)

        self.assert_sent_json(body)

    def test_send_single_file(self):
        destination = HttpDestination({})
        body = {'p1': 5}
        destination.send('ignored', body, files=[File('log.txt', 'log content')])

        expected_body = body.copy()
        expected_body['files'] = {'log.txt': 'log content'}
        self.assert_sent_json(expected_body)

    def test_send_multiple_files(self):
        destination = HttpDestination({})
        body = {'p1': 5}
        destination.send('ignored', body, files=[
            File('log.txt', 'log content'),
            File('admin.data', 'something happened'),
            File('.hidden', '123-345-abc')])

        expected_body = body.copy()
        expected_body['files'] = {'log.txt': 'log content',
                                  'admin.data': 'something happened',
                                  '.hidden': '123-345-abc'}
        self.assert_sent_json(expected_body)

    def test_send_file_with_string_body(self):
        destination = HttpDestination({})
        self.assertRaisesRegex(Exception, 'Files are supported only for JSON body, was \'test_body\'',
                               destination.send, 'ignored', 'test_body', files=[File('log.txt', 'log content')])

    def assert_sent_data(self, body, content_type=None):
        self.assertEqual([{'body': body, 'content_type': content_type}],
                         self.get_communicators()[0].captured_arguments)

    def assert_sent_json(self, body):
        arguments = self.get_communicators()[0].captured_arguments[0]

        self.assertEqual('application/json', arguments['content_type'])

        actual_body = arguments['body']
        actual_body_parsed = json.loads(actual_body)
        self.assertEqual(body, actual_body_parsed)
