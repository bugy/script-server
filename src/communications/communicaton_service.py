import logging
import threading

_THREAD_PREFIX = 'CommunicationThread-'

LOGGER = logging.getLogger('script_server.communication_service')


class CommunicationsService:

    def __init__(self, destinations) -> None:
        self._destinations = destinations

    def send(self, title, body, files=None):
        if not self._destinations:
            return

        def _send():
            for destination in self._destinations:
                try:
                    destination.send(title, body, files)
                except:
                    LOGGER.exception('Could not send message to ' + str(destination))

        thread = threading.Thread(target=_send, name=_THREAD_PREFIX + title)
        thread.start()

    @staticmethod
    def _wait():
        for thread in threading.enumerate():
            if thread.name.startswith(_THREAD_PREFIX):
                thread.join()
