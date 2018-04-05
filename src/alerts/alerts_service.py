import logging
import threading

LOGGER = logging.getLogger('script_server.alerts_service')


class AlertsService:
    def __init__(self, alerts_config):
        if alerts_config:
            self._destinations = alerts_config.get_destinations()
        else:
            self._destinations = []

        self._running_threads = []

    def send_alert(self, title, body, logs=None):
        if not self._destinations:
            return

        def _send():
            for destination in self._destinations:
                try:
                    destination.send(title, body, logs)
                except:
                    LOGGER.exception("Couldn't send alert to " + str(destination))

        thread = threading.Thread(target=_send, name='AlertThread-' + title)
        thread.start()

    @staticmethod
    def _wait():
        for thread in threading.enumerate():
            if thread.name.startswith('AlertThread-'):
                thread.join()
