import logging
from collections import OrderedDict

from communications.communicaton_service import CommunicationsService
from communications.destination_script import ScriptDestination
from execution.execution_service import ExecutionService
from model.model_helper import read_bool_from_config, read_list
from utils.process_utils import ProcessInvoker

LOGGER = logging.getLogger('script_server.execution_callbacks')

_EXIT_CODE_FIELD = 'exit_code'
_DEFAULT_NOTIFICATION_FIELDS = ['execution_id', 'pid', 'script_name', 'user', _EXIT_CODE_FIELD]


def _init_destinations(destinations_config, process_invoker: ProcessInvoker):
    destinations = []

    for destination_config in destinations_config:
        destination_type = destination_config.get('type')

        if destination_type == 'email':
            import communications.destination_email as email
            destination = email.EmailDestination(destination_config)
        elif destination_type == 'http':
            import communications.destination_http as http
            destination = http.HttpDestination(destination_config)
        elif destination_type == 'script':
            destination = ScriptDestination(destination_config, process_invoker)
        else:
            raise Exception('Unknown destination type: ' + destination_type)

        destinations.append(destination)

    return destinations


class ExecutionsCallbackFeature:
    def __init__(self,
                 execution_service: ExecutionService,
                 config,
                 process_invoker: ProcessInvoker):
        self._execution_service = execution_service

        if config is None:
            self.notify_on_start = False
            self.notify_on_finish = False
            return

        self.notify_on_start = read_bool_from_config('notify_on_start', config, default=True)
        self.notify_on_finish = read_bool_from_config('notify_on_finish', config, default=True)

        destinations_config = read_list(config, 'destinations', [])
        if not destinations_config:
            LOGGER.warning('Execution callback destinations are missing! Please specify any')
            self.notify_on_start = False
            self.notify_on_finish = False
            return

        destinations = _init_destinations(destinations_config, process_invoker)
        self._communication_service = CommunicationsService(destinations)

        self.notification_fields = read_list(config, 'notification_fields', default=_DEFAULT_NOTIFICATION_FIELDS)

    def _subscribe_execution_listener(self):
        execution_service = self._execution_service

        if self.notify_on_start:
            def started(execution_id, user):
                notification_object = self.prepare_notification_object(execution_id, 'execution_started', user)
                if _EXIT_CODE_FIELD in notification_object:
                    del notification_object[_EXIT_CODE_FIELD]
                title = 'Execution ' + str(execution_id) + ' started'

                self._communication_service.send(title, notification_object)

            execution_service.add_start_listener(started)

        if self.notify_on_finish:
            def finished(execution_id, user):
                notification_object = self.prepare_notification_object(execution_id, 'execution_finished', user)

                title = 'Execution ' + str(execution_id) + ' finished'
                self._communication_service.send(title, notification_object)

            execution_service.add_finish_listener(finished)

    def start(self):
        self._subscribe_execution_listener()

    def prepare_notification_object(self, execution_id, event_type, user):
        execution_service = self._execution_service
        pid = execution_service.get_process_id(execution_id)
        script_name = execution_service.get_config(execution_id, user).name

        notification_object = OrderedDict()

        notification_object['execution_id'] = execution_id
        notification_object['pid'] = pid
        notification_object['script_name'] = script_name
        notification_object['user'] = user.user_id
        notification_object[_EXIT_CODE_FIELD] = execution_service.get_exit_code(execution_id)

        all_fields = list(notification_object.keys())
        for field in all_fields:
            if field not in self.notification_fields:
                del notification_object[field]

        notification_object['event_type'] = event_type
        notification_object.move_to_end('event_type', False)

        return notification_object

    # tests only
    def _wait(self):
        self._communication_service._wait()
