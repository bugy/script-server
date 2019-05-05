import logging
from collections import OrderedDict

from communications import destination_base
from communications.communicaton_service import CommunicationsService
from model.model_helper import read_list

LOGGER = logging.getLogger('script_server.alerts_service')


def _init_destinations(destinations_config):
    destinations = []

    for destination_config in destinations_config:
        destination_type = destination_config.get('type')

        if destination_type == 'email':
            import communications.destination_email as email
            destination = email.EmailDestination(destination_config)
        elif destination_type == 'http':
            destination = _HttpDestinationWrapper(destination_config)
        else:
            raise Exception('Unknown alert destination type: ' + destination_type)

        destinations.append(destination)

    return destinations


class AlertsService:
    def __init__(self, alerts_config):
        if alerts_config:
            destinations_config = read_list(alerts_config, 'destinations', [])
        else:
            destinations_config = []

        destinations = _init_destinations(destinations_config)
        self._communication_service = CommunicationsService(destinations)

    def send_alert(self, title, body, files=None):
        self._communication_service.send(title, body, files)

    def _wait(self):
        self._communication_service._wait()


class _HttpDestinationWrapper(destination_base.Destination):
    def __init__(self, params_dict):
        import communications.destination_http as http
        self._destination = http.HttpDestination(params_dict)

    def send(self, title, body, files=None):
        data = OrderedDict([('title', title), ('message', body)])

        self._destination.send(title, data, files=files)

    def __str__(self) -> str:
        return 'Wrapped ' + str(self._destination)
