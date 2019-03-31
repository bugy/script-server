import importlib
import json
import sys
import unittest
from unittest import mock

from communications import alerts_service
from communications.alerts_service import AlertsService
from communications.communication_model import File
from communications.communicaton_service import CommunicationsService
from communications.destination_base import Destination
from tests.communications.communication_test_utils import MockDestination, mock_communicators


class TestCommunicationService(unittest.TestCase):
    def test_send_single_destination(self):
        destination = self.create_destination()
        service = self.create_service(destination)

        service.send('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination.messages))
        self.validate_message(destination.messages[0], 'title', 'body')

    def test_no_destinations(self):
        service = self.create_service()
        service.send('title', 'body')
        service._wait()

    def test_3_sequential_alerts(self):
        destination = self.create_destination()
        service = self.create_service(destination)

        service.send('title 1', 'body 1')
        service.send('title 2', 'body 2')
        service.send('title 3', 'body 3')
        service._wait()

        self.assertEqual(3, len(destination.messages))
        self.validate_message(destination.messages[0], 'title 1', 'body 1')
        self.validate_message(destination.messages[1], 'title 2', 'body 2')
        self.validate_message(destination.messages[2], 'title 3', 'body 3')

    def test_2_destinations(self):
        destination1 = self.create_destination()
        destination2 = self.create_destination()
        service = self.create_service(destination1, destination2)

        service.send('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination1.messages))
        self.assertEqual(1, len(destination2.messages))

    def test_2_destinations_when_one_failing(self):
        destination1 = self.create_failing_destination()
        destination2 = self.create_destination()
        service = self.create_service(destination1, destination2)

        service.send('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination2.messages))

    def create_destination(self):
        return MockDestination('mockDestination')

    @staticmethod
    def create_failing_destination():
        class FailingDestination(Destination):
            def send(self, title, body, files=None):
                raise Exception('Send failed')

        return FailingDestination()

    def create_service(self, *destinations):
        return CommunicationsService(destinations)

    def validate_message(self, message_tuple, title, body, files=None):
        message_title, message_body, message_logs = message_tuple

        self.assertEqual(title, message_title)
        self.assertEqual(body, message_body)
        self.assertEqual(files, message_logs)


@mock_communicators
class TestAlertsService(unittest.TestCase):
    def test_create_single_http_destination(self):
        config = self.create_config(['http'])
        AlertsService(config)

        self.assert_created_destinations(['http1'])

    def test_create_single_email_destination(self):
        config = self.create_config(['email'])
        AlertsService(config)

        self.assert_created_destinations(['email1'])

    def test_create_for_missing_config(self):
        AlertsService(None)

        self.assert_created_destinations([])

    def test_create_mixed_destinations(self):
        config = self.create_config(['email', 'http', 'http', 'email'])
        AlertsService(config)

        self.assert_created_destinations(['email1', 'http1', 'http2', 'email2'])

    def test_create_unknown_destination(self):
        config = self.create_config(['socket'])
        self.assertRaisesRegex(Exception, 'Unknown alert destination type: socket', AlertsService, config)

        self.assert_created_destinations([])

    def test_send_email_alert(self):
        config = self.create_config(['email'])
        alerts_service = AlertsService(config)

        title = 'My test alert'
        body = 'Test message body'
        files = [File(filename='log.txt', content='doing X')]

        self.send_alert(alerts_service, body, files, title)

        self.assertEqual([(title, body, files)], self.get_communicators()[0].messages)

    def test_send_http_alert(self):
        config = self.create_config(['http'])
        alerts_service = AlertsService(config)

        title = 'My test alert'
        body = 'Test message body'
        files = [File(filename='log.txt', content='doing X')]

        self.send_alert(alerts_service, body, files, title)

        expected_body = json.dumps({
            'title': title,
            'message': body,
            'files': {
                'log.txt': 'doing X'
            }})
        self.assertEqual([(None, expected_body, None)], self.get_communicators()[0].messages)

    def test_import_alerts_service_with_missing_dependencies(self):
        with mock.patch.dict(sys.modules, {'requests': None}):
            with mock.patch.dict(sys.modules, {'smtplib': None}):
                importlib.reload(alerts_service)

    def send_alert(self, alerts_service, body, files, title):
        alerts_service.send_alert(title, body, files=files)
        alerts_service._wait()

    def create_config(self, types):
        destinations = [{'type': t} for t in types]
        config = {'destinations': destinations}
        return config

    def assert_created_destinations(self, expected_names):
        communicators = self.get_communicators()
        actual_names = [d.name for d in communicators]

        self.assertEqual(expected_names, actual_names)
