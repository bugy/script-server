from unittest.mock import patch

from communications.destination_base import Destination


def mock_communicators(cls):
    original_set_up = getattr(cls, 'setUp')
    original_tear_down = getattr(cls, 'tearDown')

    def setUp(self):
        self.communicators_mock = CommunicatorsMock()

        original_set_up(self)

    def tearDown(self):
        self.communicators_mock.stop()

        original_tear_down(self)

    def get_communicators(self):
        return self.communicators_mock.communicators

    setattr(cls, 'setUp', setUp)
    setattr(cls, 'tearDown', tearDown)
    setattr(cls, 'get_communicators', get_communicators)

    return cls


class CommunicatorsMock:

    def __init__(self) -> None:
        communicators = []
        self.communicators = communicators

        def communicator_generator(name, mock_class):
            counter = 0

            def creator(config):
                nonlocal counter
                counter += 1
                communicator = mock_class(name + str(counter))
                communicators.append(communicator)
                return communicator

            return creator

        self.http_patch = patch('communications.destination_http._create_communicator')
        http_patched_func = self.http_patch.start()
        http_patched_func.side_effect = communicator_generator('http', MockHttpCommunicator)

        self.email_patch = patch('communications.destination_email._create_communicator')
        email_patched_func = self.email_patch.start()
        email_patched_func.side_effect = communicator_generator('email', MockEmailCommunicator)

    def stop(self):
        self.http_patch.stop()
        self.email_patch.stop()


class MockDestination(Destination):
    def __init__(self, name) -> None:
        self.messages = []
        self.name = name

    def send(self, title, body, files=None):
        message = (title, body, files)
        self.messages.append(message)


class MockEmailCommunicator:
    def __init__(self, name) -> None:
        self.messages = []
        self.name = name

    def send(self, title, body, files=None):
        message = (title, body, files)
        self.messages.append(message)


class MockHttpCommunicator:
    def __init__(self, name) -> None:
        self.messages = []
        self.captured_arguments = []
        self.name = name

    def send(self, body, content_type=None):
        message = (None, body, None)
        self.messages.append(message)
        self.captured_arguments.append({'body': body, 'content_type': content_type})
