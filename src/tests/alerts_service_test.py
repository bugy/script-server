import unittest

from communications.alerts_service import AlertsService
from communications.destination_base import Destination
from model.server_conf import AlertsConfig


class TestAlertsService(unittest.TestCase):
    def test_send_single_alert(self):
        destination = self.create_destination()
        service = self.create_service(destination)

        service.send_alert('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination.alerts))
        self.validate_alert(destination.alerts[0], 'title', 'body')

    def test_no_destinations(self):
        service = self.create_service()
        service.send_alert('title', 'body')
        service._wait()

    def test_3_sequential_alerts(self):
        destination = self.create_destination()
        service = self.create_service(destination)

        service.send_alert('title 1', 'body 1')
        service.send_alert('title 2', 'body 2')
        service.send_alert('title 3', 'body 3')
        service._wait()

        self.assertEqual(3, len(destination.alerts))
        self.validate_alert(destination.alerts[0], 'title 1', 'body 1')
        self.validate_alert(destination.alerts[1], 'title 2', 'body 2')
        self.validate_alert(destination.alerts[2], 'title 3', 'body 3')

    def test_2_destinations(self):
        destination1 = self.create_destination()
        destination2 = self.create_destination()
        service = self.create_service(destination1, destination2)

        service.send_alert('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination1.alerts))
        self.assertEqual(1, len(destination2.alerts))

    def test_2_destinations_when_one_failing(self):
        destination1 = self.create_failing_destination()
        destination2 = self.create_destination()
        service = self.create_service(destination1, destination2)

        service.send_alert('title', 'body')
        service._wait()

        self.assertEqual(1, len(destination2.alerts))

    def create_destination(self):
        class MockDestination(Destination):
            def __init__(self) -> None:
                self.alerts = []

            def send(self, title, body, logs=None):
                alert = (title, body, logs)
                self.alerts.append(alert)

        return MockDestination()

    @staticmethod
    def create_failing_destination():
        class FailingDestination(Destination):
            def send(self, title, body, logs=None):
                raise Exception('Send failed')

        return FailingDestination()

    def create_service(self, *destinations):
        alerts_config = AlertsConfig()
        for destination in destinations:
            alerts_config.add_destination(destination)

        return AlertsService(alerts_config)

    def validate_alert(self, alert_tuple, title, body, logs=None):
        alert_title, alert_body, alert_logs = alert_tuple

        self.assertEqual(title, alert_title)
        self.assertEqual(body, alert_body)
        self.assertEqual(logs, alert_logs)
