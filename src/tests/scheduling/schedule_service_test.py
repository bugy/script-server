import json
import os
import time
from datetime import timedelta
from typing import Sequence
from unittest import TestCase
from unittest.mock import patch, ANY, MagicMock

from auth.user import User
from config.config_service import ConfigService
from scheduling import scheduler
from scheduling.schedule_config import ScheduleConfig, InvalidScheduleException
from scheduling.schedule_service import ScheduleService, InvalidUserException, UnavailableScriptException
from scheduling.scheduling_job import SchedulingJob
from tests import test_utils
from tests.test_utils import AnyUserAuthorizer
from utils import date_utils, audit_utils, file_utils

mocked_now = date_utils.parse_iso_datetime('2020-07-24T12:30:59.000000Z')
mocked_now_epoch = mocked_now.timestamp()


class ScheduleServiceTestCase(TestCase):
    def assert_schedule_calls(self, expected_job_path_time_tuples):
        self.assertEqual(len(expected_job_path_time_tuples), len(self.scheduler_mock.enterabs.call_args_list))

        for i, expected_tuple in enumerate(expected_job_path_time_tuples):
            expected_job = expected_tuple[0]
            expected_job_path = expected_tuple[1]
            expected_time = date_utils.sec_to_datetime(expected_tuple[2])

            # the first item of call_args is actual arguments, passed to the method
            args = self.scheduler_mock.enterabs.call_args_list[i][0]

            # we schedule job as enterabs(expected_time, priority, self._execute_job, (job, job_path))
            schedule_method_args_tuple = args[3]
            actual_job_arg = schedule_method_args_tuple[0]
            actual_job_path_arg = schedule_method_args_tuple[1]
            actual_time = date_utils.sec_to_datetime(args[0])

            self.assertEqual(expected_job_path, actual_job_path_arg)
            self.assertEqual(expected_time, actual_time)
            self.assertDictEqual(expected_job.as_serializable_dict(),
                                 actual_job_arg.as_serializable_dict())

    def mock_schedule_model_with_secure_param(self):
        self.create_config('secure-config', parameters=[
            {'name': 'p1', 'secure': True},
            {'name': 'param_2', 'type': 'multiselect', 'values': ['hello', 'world', '1', '2', '3']},
        ])

    def setUp(self) -> None:
        super().setUp()
        test_utils.setup()

        self.patcher = patch('sched.scheduler')
        self.scheduler_mock = MagicMock()
        self.patcher.start().return_value = self.scheduler_mock

        scheduler._sleep = MagicMock()
        scheduler._sleep.side_effect = lambda x: time.sleep(0.001)

        self.config_service = ConfigService(AnyUserAuthorizer(), test_utils.temp_folder, test_utils.process_invoker)

        self.create_config('my_script_A')
        self.create_config('unschedulable-script', scheduling_enabled=False)

        self.execution_service = MagicMock()
        self.execution_service.start_script.side_effect = lambda config, user: time.time_ns()

        self.schedule_service = ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)

        date_utils._mocked_now = mocked_now

    def create_config(self, name, scheduling_enabled=True, parameters=None, auto_cleanup=False):
        if parameters is None:
            parameters = [
                {'name': 'p1', 'values_ui_mapping': {'bingo!': 'mpd'}},
                {'name': 'param_2', 'type': 'multiselect', 'values': ['hello', 'world', '1', '2', '3']},
            ]

        test_utils.write_script_config(
            {
                'name': name,
                'script_path': 'echo 1',
                'parameters': parameters,
                'scheduling': {'enabled': scheduling_enabled, 'auto_cleanup': auto_cleanup}
            },
            name)

    def tearDown(self) -> None:
        super().tearDown()

        test_utils.cleanup()

        date_utils._mocked_now = None

        self.schedule_service.stop()

        scheduler._sleep = time.sleep

        self.patcher.stop()


class TestScheduleServiceCreateJob(ScheduleServiceTestCase):
    def test_create_job_when_single(self):
        job_prototype = create_job()
        job_id = self.call_create_job(job_prototype)

        self.assertEqual('1', job_id)

        job_prototype.id = job_id
        self.verify_config_files([job_prototype])

    def test_create_job_when_multiple(self):
        jobs = []

        for i in range(1, 3):
            script_name = 'script-' + str(i)
            self.create_config(script_name)

            job_prototype = create_job(
                user_id='user-' + str(i),
                script_name=script_name,
                repeatable=i % 2 == 1,
                parameter_values={'p1': 'hi', 'param_2': [str(i)]})
            job_id = self.call_create_job(job_prototype)

            self.assertEqual(str(i), job_id)

            job_prototype.id = job_id

            jobs.append(job_prototype)

        self.verify_config_files(jobs)

    def test_create_job_when_user_none(self):
        self.assertRaisesRegex(
            InvalidUserException,
            'User id is missing',
            self.schedule_service.create_job,
            'abc', {}, {}, None)

    def test_create_job_when_not_schedulable(self):
        job_prototype = create_job(script_name='unschedulable-script')

        self.assertRaisesRegex(
            UnavailableScriptException,
            'is not schedulable',
            self.call_create_job,
            job_prototype)

    def test_create_job_when_secure(self):
        self.mock_schedule_model_with_secure_param()

        job_prototype = create_job(script_name='secure-config')

        self.assertRaisesRegex(
            UnavailableScriptException,
            'secure-config is not schedulable',
            self.call_create_job,
            job_prototype)

    def test_create_job_when_non_repeatable_in_the_past(self):
        job_prototype = create_job(repeatable=False, start_datetime=mocked_now - timedelta(seconds=1))

        self.assertRaisesRegex(
            InvalidScheduleException,
            'Start date should be in the future',
            self.call_create_job,
            job_prototype)

    def test_create_job_verify_scheduler_call_when_one_time(self):
        job_prototype = create_job(id='1', repeatable=False, start_datetime=mocked_now + timedelta(seconds=97))
        self.call_create_job(job_prototype)

        self.assert_schedule_calls([(job_prototype, get_job_path(job_prototype), mocked_now_epoch + 97)])

    def test_create_job_verify_timer_call_when_repeatable(self):
        job_prototype = create_job(id='1', repeatable=True, start_datetime=mocked_now - timedelta(seconds=97))
        self.call_create_job(job_prototype)

        self.assert_schedule_calls([(job_prototype, get_job_path(job_prototype), mocked_now_epoch + 1468703)])

    def test_create_job_when_ui_values_mapping(self):
        job_prototype = create_job(
            id='1',
            parameter_values={'p1': 'mpd', 'param_2': []},
            repeatable=False)
        self.call_create_job(job_prototype)

        self.assert_schedule_calls([(job_prototype, get_job_path(job_prototype), mocked_now_epoch + 5)])

    def call_create_job(self, job: SchedulingJob):
        return self.schedule_service.create_job(
            job.script_name,
            job.parameter_values,
            job.schedule.as_serializable_dict(),
            job.user)

    def verify_config_files(self, expected_jobs: Sequence[SchedulingJob]):
        expected_files = [get_job_filename(job) for job in expected_jobs]

        schedules_dir = os.path.join(test_utils.temp_folder, 'schedules')
        test_utils.assert_dir_files(expected_files, schedules_dir, self)

        for job in expected_jobs:
            job_path = os.path.join(schedules_dir, get_job_filename(job))
            content = file_utils.read_file(job_path)
            restored_job = json.loads(content)

            self.assertEqual(restored_job, job.as_serializable_dict())


class TestScheduleServiceInit(ScheduleServiceTestCase):
    def test_no_config_folder(self):
        schedule_service = ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)

        self.assertEqual('1', schedule_service._id_generator.next_id())
        self.assert_schedule_calls([])

    def test_restore_multiple_configs(self):
        job1 = create_job(id='11', start_datetime=mocked_now + timedelta(seconds=10), repeatable=False)
        job2 = create_job(id=9, start_datetime=mocked_now + timedelta(seconds=20), repeatable=False)
        job3 = create_job(id=3, start_datetime=mocked_now + timedelta(seconds=30), repeatable=False)
        job1_path = save_job(job1)
        job2_path = save_job(job2)
        job3_path = save_job(job3)

        schedule_service = ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assertEqual('12', schedule_service._id_generator.next_id())
        self.assert_schedule_calls([
            # alphabetical order, ids 11 -> 3 -> 9;
            (job1, job1_path, mocked_now_epoch + 10),
            (job3, job3_path, mocked_now_epoch + 30),
            (job2, job2_path, mocked_now_epoch + 20)
        ])

    def test_restore_configs_when_one_corrupted(self):
        job1 = create_job(id='11', repeatable=None)
        job2 = create_job(id=3, repeatable=False, start_datetime=mocked_now + timedelta(seconds=10))
        save_job(job1)
        job2_path = save_job(job2)

        schedule_service = ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assertEqual('12', schedule_service._id_generator.next_id())
        self.assert_schedule_calls([
            (job2, job2_path, mocked_now_epoch + 10)
        ])

    def test_schedule_on_restore_when_one_time(self):
        job = create_job(id=3, repeatable=False, start_datetime=mocked_now + timedelta(minutes=3))
        job_path = save_job(job)

        ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 180)])

    def test_schedule_on_restore_when_one_time_in_past(self):
        job = create_job(id=3, repeatable=False, start_datetime=mocked_now - timedelta(seconds=1))
        save_job(job)

        ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assert_schedule_calls([])

    def test_schedule_on_restore_when_repeatable_in_future(self):
        job = create_job(id=3, repeatable=True, start_datetime=mocked_now + timedelta(hours=3))
        job_path = save_job(job)

        ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 1479600)])

    def test_schedule_on_restore_when_repeatable_in_past(self):
        job = create_job(id=3, repeatable=True, start_datetime=mocked_now + timedelta(days=2))
        job_path = save_job(job)

        ScheduleService(self.config_service, self.execution_service, test_utils.temp_folder)
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 1468800)])

    def test_scheduler_runner(self):
        original_runs_count = self.scheduler_mock.run.call_count
        time.sleep(0.1)
        step1_runs_count = self.scheduler_mock.run.call_count

        self.assertGreater(step1_runs_count, original_runs_count)

        time.sleep(0.1)
        step2_runs_count = self.scheduler_mock.run.call_count
        self.assertGreater(step2_runs_count, step1_runs_count)

    def test_scheduler_runner_when_stopped(self):
        self.schedule_service.stop()
        time.sleep(0.1)
        original_runs_count = self.scheduler_mock.run.call_count

        time.sleep(0.1)

        final_runs_count = self.scheduler_mock.run.call_count
        self.assertEqual(final_runs_count, original_runs_count)


class TestScheduleServiceExecuteJob(ScheduleServiceTestCase):
    def test_execute_simple_job(self):
        job = create_job(
            id=1,
            repeatable=False,
            start_datetime=mocked_now - timedelta(seconds=1),
            parameter_values={'p1': 'mpd', 'param_2': ['hello', '3']})

        job_path = save_job(job)

        self.schedule_service._execute_job(job, job_path)

        self.verify_start_script_call({'p1': 'bingo!', 'param_2': ['hello', '3']}, job.user)

        self.execution_service.add_finish_listener.assert_not_called()
        self.assert_schedule_calls([])

    def test_execute_repeatable_job(self):
        job = create_job(id=1,
                         repeatable=True,
                         start_datetime=mocked_now - timedelta(seconds=1),
                         repeat_unit='days',
                         repeat_period=1)
        job_path = save_job(job)

        self.schedule_service._execute_job(job, job_path)

        self.verify_start_script_call(job.parameter_values, job.user)
        self.execution_service.add_finish_listener.assert_not_called()
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 86399)])

    def test_execute_when_fails(self):
        job = create_job(id=1,
                         repeatable=True,
                         start_datetime=mocked_now - timedelta(seconds=1),
                         repeat_unit='days',
                         repeat_period=1)
        job_path = save_job(job)

        self.execution_service.start_script.side_effect = Exception('Test exception')
        self.schedule_service._execute_job(job, job_path)

        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 86399)])

    def test_execute_when_not_schedulable(self):
        job = create_job(id=1,
                         script_name='unschedulable-script',
                         repeatable=True,
                         start_datetime=mocked_now - timedelta(seconds=1),
                         repeat_unit='days',
                         repeat_period=1)
        job_path = save_job(job)

        self.schedule_service._execute_job(job, job_path)

        self.execution_service.start_script.assert_not_called()
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 86399)])

    def test_execute_when_has_secure_parameters(self):
        job = create_job(id=1,
                         script_name='secure-config',
                         repeatable=True,
                         start_datetime=mocked_now - timedelta(seconds=1),
                         repeat_unit='days',
                         repeat_period=1)
        job_path = save_job(job)

        self.mock_schedule_model_with_secure_param()

        self.schedule_service._execute_job(job, job_path)

        self.execution_service.start_script.assert_not_called()
        self.assert_schedule_calls([(job, job_path, mocked_now_epoch + 86399)])

    def test_execute_when_deleted(self):
        job = create_job(id=1,
                         script_name='secure-config',
                         repeatable=True,
                         start_datetime=mocked_now - timedelta(seconds=1),
                         repeat_unit='days',
                         repeat_period=1)
        job_path = save_job(job)
        os.remove(job_path)

        self.schedule_service._execute_job(job, job_path)

        self.execution_service.start_script.assert_not_called()
        self.assert_schedule_calls([])

    def test_cleanup_execution(self):
        self.create_config('script_with_cleanup', auto_cleanup=True)
        job = create_job(id=1,
                         script_name='script_with_cleanup',
                         repeatable=False,
                         start_datetime=mocked_now - timedelta(seconds=1))
        job_path = save_job(job)

        finish_callback = None

        def add_finish_listener(callback_param, execution_id):
            self.assertIsNotNone(execution_id)
            nonlocal finish_callback
            finish_callback = callback_param

        self.execution_service.add_finish_listener.side_effect = add_finish_listener

        self.schedule_service._execute_job(job, job_path)

        self.verify_start_script_call(job.parameter_values, job.user)
        self.execution_service.cleanup_execution.assert_not_called()
        self.assertIsNotNone(finish_callback)

        # noinspection PyCallingNonCallable
        finish_callback()

        self.execution_service.cleanup_execution.assert_called_once_with(ANY, job.user)

    def verify_start_script_call(self, expected_values, expected_user):
        start_args = self.execution_service.start_script.call_args[0]
        self.assertEqual(expected_user, start_args[1])
        actual_values = {name: value.mapped_script_value for name, value in start_args[0].parameter_values.items()}
        self.assertEqual(expected_values, actual_values)


def create_job(id=None,
               user_id='UserX',
               script_name='my_script_A',
               audit_names=None,
               repeatable=True,
               start_datetime=mocked_now + timedelta(seconds=5),
               repeat_unit=None,
               repeat_period=None,
               weekdays=None,
               parameter_values=None):
    if audit_names is None:
        audit_names = {audit_utils.HOSTNAME: 'my-host'}

    if repeatable and repeat_unit is None:
        repeat_unit = 'weeks'
    if repeatable and repeat_period is None:
        repeat_period = 3

    if weekdays is None and repeatable and repeat_unit == 'weeks':
        weekdays = ['monday', 'wednesday']

    if parameter_values is None:
        parameter_values = {'p1': 987, 'param_2': ['hello', 'world']}

    schedule_config = ScheduleConfig(repeatable, start_datetime)
    schedule_config.repeat_unit = repeat_unit
    schedule_config.repeat_period = repeat_period
    schedule_config.weekdays = weekdays

    return SchedulingJob(id, User(user_id, audit_names), schedule_config, script_name, parameter_values)


def get_job_filename(job):
    return job.script_name + '_' + job.user.get_audit_name() + '_' + str(job.id) + '.json'


def save_job(job):
    path = get_job_path(job)
    content = json.dumps(job.as_serializable_dict())
    file_utils.write_file(path, content)

    return path


def get_job_path(job):
    schedules_dir = os.path.join(test_utils.temp_folder, 'schedules')
    path = os.path.join(schedules_dir, get_job_filename(job))
    return path
