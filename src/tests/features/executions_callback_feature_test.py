import json
import unittest
from collections import defaultdict, OrderedDict

from communications import destination_email
from features.executions_callback_feature import ExecutionsCallbackFeature
from tests.communications.communication_test_utils import mock_communicators
from tests.test_utils import create_config_model
from utils.string_utils import values_to_string


@mock_communicators
class TestExecutionsCallbackFeature(unittest.TestCase):
    def test_init_http_communicator(self):
        self.create_feature(['http'])

        self.assert_created_destinations(['http1'])

    def test_init_email_communicator(self):
        self.create_feature(['email'])

        self.assert_created_destinations(['email1'])

    def test_init_script_communicator(self):
        self.create_feature(['script'])

        self.assert_created_destinations(['script1'])

    def test_init_mixed_communicators(self):
        self.create_feature(['email', 'http', 'http', 'script', 'email'])

        self.assert_created_destinations(['email1', 'http1', 'http2', 'script1', 'email2'])

    def test_unknown_communicator(self):
        self.assertRaisesRegex(Exception, 'Unknown destination type: socket',
                               self.create_feature, ['socket'])

        self.assert_created_destinations([])

    def test_init_empty_config(self):
        # noinspection PyTypeChecker
        feature = ExecutionsCallbackFeature(self, None)
        self.assertFalse(feature.notify_on_start)

    def test_default_on_start(self):
        feature = self.create_feature(['http'])

        self.assertTrue(feature.notify_on_start)

    def test_on_start_true(self):
        feature = self.create_feature(['http'], on_start=True)

        self.assertTrue(feature.notify_on_start)

    def test_on_start_false(self):
        feature = self.create_feature(['http'], on_start=False)

        self.assertFalse(feature.notify_on_start)

    def test_default_on_finish(self):
        feature = self.create_feature(['http'])

        self.assertTrue(feature.notify_on_finish)

    def test_on_finish_true(self):
        feature = self.create_feature(['http'], on_finish=True)

        self.assertTrue(feature.notify_on_finish)

    def test_on_finish_false(self):
        feature = self.create_feature(['http'], on_finish=False)

        self.assertFalse(feature.notify_on_finish)

    def test_on_start_when_empty_destinations(self):
        feature = self.create_feature([], on_start=True)

        self.assertFalse(feature.notify_on_start)

    def test_on_finish_when_empty_destinations(self):
        feature = self.create_feature([], on_finish=True)

        self.assertFalse(feature.notify_on_finish)

    def test_send_started_callback_to_http_destination(self):
        feature = self.create_feature(['http'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_started(123)

        self.assert_messages([123], 'execution_started')

    def test_send_finished_callback_to_http_destination(self):
        feature = self.create_feature(['http'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_finished(123)

        self.assert_messages([123], 'execution_finished')

    def test_send_started_callback_to_email_destination(self):
        feature = self.create_feature(['email'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_started(123)

        self.assert_messages([123], 'execution_started')

    def test_send_finished_callback_to_email_destination(self):
        feature = self.create_feature(['email'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_finished(123)

        self.assert_messages([123], 'execution_finished')

    def test_send_started_callback_to_script_destination(self):
        feature = self.create_feature(['script'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_started(123)

        self.assert_messages([123], 'execution_started')

    def test_send_finished_callback_to_script_destination(self):
        feature = self.create_feature(['script'])
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_finished(123)

        self.assert_messages([123], 'execution_finished')

    def test_started_callback_when_disabled(self):
        feature = self.create_feature(['http'], on_start=False)
        feature.start()

        self.fire_started(123)

        self.assert_messages([], self.get_communicators()[0].messages)

    def test_finished_callback_when_disabled(self):
        feature = self.create_feature(['http'], on_finish=False)
        feature.start()

        self.fire_finished(123)

        self.assert_messages([], self.get_communicators()[0].messages)

    def test_custom_fields_on_start(self):
        fields = ['execution_id', 'user', 'exit_code']

        feature = self.create_feature(['http', 'email'], notification_fields=fields)
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_started(123)

        self.assert_messages([123], 'execution_started', fields)

    def test_custom_fields_on_finish(self):
        fields = ['pid']

        feature = self.create_feature(['http', 'email'], notification_fields=fields)
        feature.start()

        self.add_execution(123, 'userX', 666, 13, 'my_script')
        self.fire_finished(123)

        self.assert_messages([123], 'execution_finished', fields)

    def create_feature(self, types, on_start=True, on_finish=True, notification_fields=None):
        destinations = [{'type': t} for t in types]
        config = {
            'notify_on_start': on_start,
            'notify_on_finish': on_finish,
            'destinations': destinations}

        if notification_fields is not None:
            config['notification_fields'] = notification_fields

        # noinspection PyTypeChecker
        self.callback_feature = ExecutionsCallbackFeature(self, config)
        return self.callback_feature

    def assert_created_destinations(self, expected_names):
        communicators = self.get_communicators()
        actual_names = [d.name for d in communicators]

        self.assertEqual(expected_names, actual_names)

    def assert_messages(self, execution_ids, message_type, custom_fields=None):
        for communicator in self.get_communicators():
            expected_messages = []
            for execution_id in execution_ids:
                body_object = self.build_expected_body(execution_id, message_type, custom_fields)
                body = self.format_body(body_object, communicator)
                title = self.build_title(message_type, communicator, execution_id)

                expected_messages.append((title, body, None))

            self.assertEqual(expected_messages, communicator.messages)

    def build_expected_body(self, execution_id, message_type, custom_fields=None):
        execution_info = self.execution_infos[execution_id]

        body_object = OrderedDict()
        body_object['event_type'] = message_type
        body_object['execution_id'] = execution_id
        body_object['pid'] = execution_info.pid
        body_object['script_name'] = execution_info.script_name
        body_object['user'] = execution_info.owner

        if message_type != 'execution_started':
            body_object['exit_code'] = execution_info.exit_code

        if custom_fields is not None:
            extra_fields = set(body_object.keys()) - set(custom_fields)
            extra_fields.remove('event_type')

            for key in extra_fields:
                del body_object[key]

        return body_object

    def format_body(self, body, communicator):
        if communicator.name.startswith('email'):
            return destination_email._body_dict_to_message(body)
        elif communicator.name.startswith('http'):
            return json.dumps(body)
        elif communicator.name.startswith('script'):
            return values_to_string(list(body.values()))

        return body

    def build_title(self, event_type, communicator, execution_id):
        if communicator.name.startswith('http') or communicator.name.startswith('script'):
            return None

        if event_type == 'execution_started':
            return 'Execution ' + str(execution_id) + ' started'
        elif event_type == 'execution_finished':
            return 'Execution ' + str(execution_id) + ' finished'

        return 'Wrong title in the message'

    def setUp(self):
        self.finish_listeners = []
        self.start_listeners = []

        self.execution_infos = defaultdict(lambda: _ExecutionInfo(None, None, None, None, None))

    def add_finish_listener(self, listener):
        self.finish_listeners.append(listener)

    def add_start_listener(self, listener):
        self.start_listeners.append(listener)

    def add_execution(self, execution_id, owner, pid, exit_code, script_name):
        self.execution_infos[execution_id] = _ExecutionInfo(execution_id, owner, pid, exit_code, script_name)

    def get_process_id(self, execution_id):
        return self.execution_infos[execution_id].pid

    def get_config(self, execution_id):
        if execution_id in self.execution_infos:
            return create_config_model(self.execution_infos[execution_id].script_name)

        return None

    def get_owner(self, execution_id):
        return self.execution_infos[execution_id].owner

    def get_exit_code(self, execution_id):
        return self.execution_infos[execution_id].exit_code

    def fire_started(self, execution_id):
        for listener in self.start_listeners:
            listener(execution_id)

        if self.callback_feature:
            self.callback_feature._wait()

    def fire_finished(self, execution_id):
        for listener in self.finish_listeners:
            listener(execution_id)

        if self.callback_feature:
            self.callback_feature._wait()


class _ExecutionInfo:
    def __init__(self, execution_id, owner, pid, exit_code, script_name) -> None:
        self.script_name = script_name
        self.exit_code = exit_code
        self.pid = pid
        self.owner = owner
        self.execution_id = execution_id
