import copy
import unittest

from parameterized import parameterized

from auth.authorization import Authorizer, ANY_USER, EmptyGroupProvider
from auth.user import User
from execution import executor
from execution.execution_service import ExecutionService
from execution.executor import create_process_wrapper
from model.model_helper import AccessProhibitedException
from model.script_config import ConfigModel
from tests import test_utils
from tests.test_utils import mock_object, create_audit_names, _MockProcessWrapper, _IdGeneratorMock
from utils import audit_utils

DEFAULT_USER_ID = 'test_user'
DEFAULT_AUDIT_NAMES = create_audit_names(auth_username=DEFAULT_USER_ID)
DEFAULT_USER = User(DEFAULT_USER_ID, DEFAULT_AUDIT_NAMES)

execution_owners = {}


class ExecutionServiceTest(unittest.TestCase):
    def test_start_script(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertEqual(self.get_last_id(), execution_id)

    def test_is_running_after_start(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertTrue(execution_service.is_running(execution_id, DEFAULT_USER))

    def test_is_running_after_stop(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)
        process = self.get_process(execution_id)
        process.stop()

        self.assertFalse(execution_service.is_running(execution_id, DEFAULT_USER))

    def test_exit_code(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)
        process = self.get_process(execution_id)
        process.finish(22)

        self.assertEqual(22, execution_service.get_exit_code(execution_id))

    def test_running_services_when_2_started(self):
        execution_service = self.create_execution_service()
        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        self.assertCountEqual([id1, id2], execution_service.get_running_executions())

    def test_running_services_when_2_started_and_1_stopped(self):
        execution_service = self.create_execution_service()
        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        execution_service.stop_script(id2, DEFAULT_USER)

        self.assertCountEqual([id1], execution_service.get_running_executions())

    @parameterized.expand([
        (DEFAULT_USER_ID,),
        (DEFAULT_USER_ID.upper(),),
    ])
    def test_active_executions_when_2_started(self, user_id):
        execution_service = self.create_execution_service()
        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        self.assertCountEqual([id1, id2], execution_service.get_active_executions(user_id))

    @parameterized.expand([
        ('another_user',),
        ('ANOTHER_USER',),
    ])
    def test_active_executions_with_different_user(self, user_id):
        execution_service = self.create_execution_service()
        self._start(execution_service)
        self._start(execution_service)

        self.assertCountEqual([], execution_service.get_active_executions(user_id))

    def test_active_executions_when_2_started_and_1_cleanup(self):
        execution_service = self.create_execution_service()
        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        self.get_process(id1).stop()
        execution_service.cleanup_execution(id1, DEFAULT_USER)

        self.assertCountEqual([id2], execution_service.get_active_executions(DEFAULT_USER_ID))

    def test_active_executor(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertTrue(execution_service.is_active(execution_id))
        self.assertIsNotNone(execution_service.get_active_executor(execution_id, DEFAULT_USER))

    def test_active_executor_after_cleanup(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.get_process(execution_id).stop()
        execution_service.cleanup_execution(execution_id, DEFAULT_USER)

        self.assertFalse(execution_service.is_active(execution_id))
        self.assertIsNone(execution_service.get_active_executor(execution_id, DEFAULT_USER))

    def test_cleanup_fails_on_active_execution(self):
        execution_service = self.create_execution_service()
        id1 = self._start(execution_service)

        self.assertRaises(Exception, execution_service.cleanup_execution, id1)

    def test_can_access_same_user(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertTrue(execution_service.can_access(execution_id, DEFAULT_USER_ID))

    def test_can_access_different_user(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertFalse(execution_service.can_access(execution_id, 'another_user'))

    def test_can_access_different_user_reversed(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service, user_id='another_user')

        self.assertFalse(execution_service.can_access(execution_id, DEFAULT_USER_ID))

    def test_get_audit_name(self):
        execution_service = self.create_execution_service()
        execution_id = self._start(execution_service)

        self.assertEqual(DEFAULT_USER_ID, execution_service.get_audit_name(execution_id))

    def test_get_user_parameter_values(self):
        parameter_values = {'x': 1, 'y': '2', 'z': 'True'}

        execution_service = self.create_execution_service()
        parameters = test_utils.create_simple_parameter_configs(list(parameter_values.keys()) + ['const'])
        parameters['const']['constant'] = True
        parameters['const']['default'] = 'abc'
        parameters['z']['no_value'] = True

        config_model = test_utils.create_config_model(
            'test_get_user_parameter_values',
            username=DEFAULT_USER_ID,
            parameters=parameters.values())
        execution_id = self._start_with_config(execution_service, config_model, parameter_values)

        self.assertEqual(parameter_values, execution_service.get_user_parameter_values(execution_id))

    def test_get_script_parameter_values(self):
        parameter_values = {'x': 1, 'y': '2', 'z': 'True'}

        execution_service = self.create_execution_service()
        parameters = test_utils.create_simple_parameter_configs(list(parameter_values.keys()) + ['const'])
        parameters['const']['constant'] = True
        parameters['const']['default'] = 'abc'
        parameters['z']['no_value'] = True

        config_model = test_utils.create_config_model(
            'test_get_user_parameter_values',
            username=DEFAULT_USER_ID,
            parameters=parameters.values())
        execution_id = self._start_with_config(execution_service, config_model, parameter_values)

        self.assertEqual({'x': 1, 'y': '2', 'z': True, 'const': 'abc'},
                         execution_service.get_script_parameter_values(execution_id))

    def test_start_listener(self):
        started_ids = []

        execution_service = self.create_execution_service()
        execution_service.add_start_listener(lambda id, user: started_ids.append(id))

        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        self.assertCountEqual([id1, id2], started_ids)

    def test_finish_listener(self):
        finished_ids = []

        execution_service = self.create_execution_service()
        execution_service.add_finish_listener(lambda id, user: finished_ids.append(id))

        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        self.assertCountEqual([], finished_ids)

        self.get_process(id2).stop()
        self.assertCountEqual([id2], finished_ids)

        self.get_process(id1).stop()
        self.assertCountEqual([id1, id2], finished_ids)

    def test_finish_listener_by_id(self):
        execution_service = self.create_execution_service()

        id1 = self._start(execution_service)
        id2 = self._start(execution_service)

        notifications = []

        execution_service.add_finish_listener(lambda: notifications.append('event'), id1)

        self.get_process(id2).stop()
        self.get_process(id1).stop()
        self.assertEqual(1, len(notifications))

    def _start(self, execution_service, user_id=DEFAULT_USER_ID):
        return _start(execution_service, user_id)

    def _start_with_config(self, execution_service, config, parameter_values=None, user_id=DEFAULT_USER_ID):
        if parameter_values is None:
            parameter_values = {}

        user = User(user_id, DEFAULT_AUDIT_NAMES)
        execution_id = execution_service.start_script(
            config,
            parameter_values,
            user)
        return execution_id

    def create_execution_service(self):
        file_download_feature = mock_object()
        file_download_feature.is_downloadable = lambda x: False

        execution_service = ExecutionService(self.authorizer, self.id_generator)
        self.exec_services.append(execution_service)
        return execution_service

    def get_process(self, execution_id) -> _MockProcessWrapper:
        return self.processes[execution_id]

    def setUp(self):
        super().setUp()
        self.id_generator = _IdGeneratorMock()
        self.authorizer = Authorizer(ANY_USER, [], [], [], EmptyGroupProvider())
        self.exec_services = []
        self.processes = {}

        def create_process(executor, command, working_directory, env_variables):
            wrapper = _MockProcessWrapper(executor, command, working_directory, env_variables)
            self.processes[self.get_last_id()] = wrapper
            return wrapper

        executor._process_creator = create_process

    def tearDown(self):
        super().tearDown()

        for service in self.exec_services:
            for id in service.get_running_executions():
                user = execution_owners[id]
                service.kill_script(id, user)

            active_exec_ids = copy.copy(service._active_executor_ids)
            for id in active_exec_ids:
                user = execution_owners[id]
                service.cleanup_execution(id, user)

    def get_last_id(self):
        return self.id_generator.generated_ids[-1]


class ExecutionServiceAuthorizationTest(unittest.TestCase):
    owner_user = User('user_x', {audit_utils.AUTH_USERNAME: 'some_name'})

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', AccessProhibitedException),
        ('history_user', AccessProhibitedException)
    ])
    def test_get_active_executor(self, user_id, expected_exception):
        self._assert_throws_exception(expected_exception,
                                      self.executor_service.get_active_executor,
                                      self.execution_id,
                                      User(user_id, {}))

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', AccessProhibitedException),
        ('history_user', AccessProhibitedException)
    ])
    def test_stop_script(self, user_id, expected_exception):
        self._assert_throws_exception(expected_exception,
                                      self.executor_service.stop_script,
                                      self.execution_id,
                                      User(user_id, {}),
                                      has_results=False)

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', AccessProhibitedException),
        ('history_user', AccessProhibitedException)
    ])
    def test_kill_script(self, user_id, expected_exception):
        self._assert_throws_exception(expected_exception,
                                      self.executor_service.kill_script,
                                      self.execution_id,
                                      User(user_id, {}),
                                      has_results=False)

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', None),
        ('history_user', None)
    ])
    def test_is_running(self, user_id, expected_exception):
        self._assert_throws_exception(expected_exception,
                                      self.executor_service.is_running,
                                      self.execution_id,
                                      User(user_id, {}))

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', AccessProhibitedException),
        ('history_user', AccessProhibitedException)
    ])
    def test_get_config(self, user_id, expected_exception):
        self._assert_throws_exception(expected_exception,
                                      self.executor_service.get_config,
                                      self.execution_id,
                                      User(user_id, {}))

    @parameterized.expand([
        (owner_user.user_id, None),
        ('another_user', AccessProhibitedException),
        ('admin_user', AccessProhibitedException),
        ('history_user', AccessProhibitedException)
    ])
    def test_cleanup(self, user_id, expected_exception):
        self.executor_service.stop_script(self.execution_id, self.owner_user)

        self._assert_throws_exception(expected_exception,
                                      self.executor_service.cleanup_execution,
                                      self.execution_id,
                                      User(user_id, {}),
                                      has_results=False)

        self.script_cleaned = True

    def _assert_throws_exception(self, expected_exception, func, *parameters, has_results=True):
        try:
            result = func(*parameters)
            if expected_exception:
                self.fail('Should throw ' + str(expected_exception) + ', but did not')
            if has_results:
                self.assertIsNotNone(result)

        except Exception as e:
            self.assertIsInstance(e, expected_exception)

    def setUp(self) -> None:
        super().setUp()

        def create_process(executor, command, working_directory, env_variables):
            return _MockProcessWrapper(executor, command, working_directory, env_variables)

        executor._process_creator = create_process

        authorizer = Authorizer([ANY_USER], ['admin_user'], ['history_user'], [], EmptyGroupProvider())
        self.executor_service = ExecutionService(authorizer, _IdGeneratorMock())

        self.execution_id = _start(self.executor_service, self.owner_user.user_id)

        self.script_cleaned = False

    def tearDown(self) -> None:
        super().tearDown()

        executor._process_creator = create_process_wrapper

        if not self.script_cleaned:
            self.executor_service.kill_script(self.execution_id, self.owner_user)
            self.executor_service.cleanup_execution(self.execution_id, self.owner_user)


def _start(execution_service, user_id=DEFAULT_USER_ID):
    return _start_with_config(execution_service, _create_script_config([]), None, user_id)


def _start_with_config(execution_service, config, parameter_values=None, user_id=DEFAULT_USER_ID):
    if parameter_values is None:
        parameter_values = {}

    user = User(user_id, DEFAULT_AUDIT_NAMES)
    execution_id = execution_service.start_script(
        config,
        parameter_values,
        user)
    execution_owners[execution_id] = user
    return execution_id


def _create_script_config(parameter_configs):
    config = ConfigModel(
        {'name': 'script_x',
         'script_path': 'ls',
         'parameters': parameter_configs},
        'script_x.json', 'user1', 'localhost')
    return config
