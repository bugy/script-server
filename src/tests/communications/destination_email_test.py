import unittest
from collections import OrderedDict

from communications.communication_model import File
from communications.destination_email import EmailDestination
from tests.communications.communication_test_utils import mock_communicators


@mock_communicators
class TestEmailDestination(unittest.TestCase):
    def test_string_body(self):
        self.send('My title', 'My body')

        self.assertEqual([('My title', 'My body', None)], self.get_sent_messages())

    def test_object_body(self):
        self.send('My title', OrderedDict([('name', 'my_script'), ('duration', 60), ('finished', True)]))

        expected_body = 'name: my_script\nduration: 60\nfinished: True'
        self.assertEqual([('My title', expected_body, None)], self.get_sent_messages())

    def test_send_files(self):
        files = [
            File('file1.txt', 'some text'),
            File('my_data.dat', b'abcdef12345'),
            File('movie.vid', path='/home/me/movies/movie.vid'),
        ]
        self.send('My title', 'my_body', files)

        self.assertEqual([('My title', 'my_body', files)], self.get_sent_messages())

    def send(self, title, body, files=None):
        EmailDestination({}).send(title, body, files)

    def get_sent_messages(self):
        return self.get_communicators()[0].messages
