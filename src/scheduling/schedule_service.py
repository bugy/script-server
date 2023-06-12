import json
import logging
import os
import sched
import threading
import time
from datetime import timedelta

from auth.user import User
from config.config_service import ConfigService
from execution.execution_service import ExecutionService
from execution.id_generator import IdGenerator
from scheduling import scheduling_job
from scheduling.schedule_config import read_schedule_config, InvalidScheduleException
from scheduling.scheduling_job import SchedulingJob
from utils import file_utils, date_utils, custom_json

SCRIPT_NAME_KEY = 'script_name'
USER_KEY = 'user'
PARAM_VALUES_KEY = 'parameter_values'

JOB_SCHEDULE_KEY = 'schedule'

LOGGER = logging.getLogger('script_server.scheduling.schedule_service')

_sleep = time.sleep


def restore_jobs(schedules_folder):
    files = [file for file in os.listdir(schedules_folder) if file.endswith('.json')]
    files.sort()

    job_path_dict = {}
    ids = []  # list of ALL ids, including broken configs

    for file in files:
        try:
            job_path = os.path.join(schedules_folder, file)
            content = file_utils.read_file(job_path)
            job_json = custom_json.loads(content)
            ids.append(job_json['id'])

            job = scheduling_job.from_dict(job_json)

            job_path_dict[job_path] = job
        except:
            LOGGER.exception('Failed to parse schedule file: ' + file)

    return job_path_dict, ids


class ScheduleService:

    def __init__(self,
                 config_service: ConfigService,
                 execution_service: ExecutionService,
                 conf_folder):
        self._schedules_folder = os.path.join(conf_folder, 'schedules')
        file_utils.prepare_folder(self._schedules_folder)

        self._config_service = config_service
        self._execution_service = execution_service

        (jobs, ids) = restore_jobs(self._schedules_folder)
        self._id_generator = IdGenerator(ids)
        self.stopped = False

        self.scheduler = sched.scheduler(timefunc=time.time)
        self._start_scheduler()

        for job_path, job in jobs.items():
            self.schedule_job(job, job_path)

    def create_job(self, script_name, parameter_values, incoming_schedule_config, user: User):
        if user is None:
            raise InvalidUserException('User id is missing')

        config_model = self._config_service.load_config_model(script_name, user, parameter_values)
        self.validate_script_config(config_model)

        schedule_config = read_schedule_config(incoming_schedule_config)

        if not schedule_config.repeatable and date_utils.is_past(schedule_config.start_datetime):
            raise InvalidScheduleException('Start date should be in the future')

        if schedule_config.endOption == 'on':
            if schedule_config.start_datetime > schedule_config.endArg:
                raise InvalidScheduleException('End date should be after start date')
            if date_utils.is_past(schedule_config.endArg):
                raise InvalidScheduleException('End date should be in the future')

        if schedule_config.endOption == 'after' and schedule_config.endArg <= 0:
            raise InvalidScheduleException('Count should be greater than 0!')

        id = self._id_generator.next_id()

        normalized_values = {}
        for parameter_name, value_wrapper in config_model.parameter_values.items():
            if value_wrapper.user_value is not None:
                normalized_values[parameter_name] = value_wrapper.user_value

        job = SchedulingJob(id, user, schedule_config, script_name, normalized_values)

        job_path = self.save_job(job)

        self.schedule_job(job, job_path)

        return id

    @staticmethod
    def validate_script_config(config_model):
        if not config_model.schedulable:
            raise UnavailableScriptException(config_model.name + ' is not schedulable')

        for parameter in config_model.parameters:
            if parameter.secure:
                raise UnavailableScriptException(
                    'Script contains secure parameters (' + parameter.str_name() + '), this is not supported')

    def schedule_job(self, job: SchedulingJob, job_path):
        schedule = job.schedule

        if not schedule.repeatable and date_utils.is_past(schedule.start_datetime):
            return
        
        if schedule.endOption == 'after' and schedule.endArg <= 0:
            return
        
        next_datetime = schedule.get_next_time()

        if schedule.endOption == 'on' and date_utils.is_past(schedule.endArg) or next_datetime < schedule.endArg:
            return
        
        LOGGER.info(
            'Scheduling ' + job.get_log_name() + ' at ' + next_datetime.astimezone(tz=None).strftime('%H:%M, %d %B %Y'))

        self.scheduler.enterabs(next_datetime.timestamp(), 1, self._execute_job, (job, job_path))

    def _execute_job(self, job: SchedulingJob, job_path):
        LOGGER.info('Executing ' + job.get_log_name())

        if not os.path.exists(job_path):
            LOGGER.info(job.get_log_name() + ' was removed, skipping execution')
            return

        script_name = job.script_name
        parameter_values = job.parameter_values
        user = job.user

        try:
            config = self._config_service.load_config_model(script_name, user, parameter_values)
            self.validate_script_config(config)

            execution_id = self._execution_service.start_script(config, user)
            LOGGER.info('Started script #' + str(execution_id) + ' for ' + job.get_log_name())

            if config.scheduling_auto_cleanup:
                def cleanup():
                    self._execution_service.cleanup_execution(execution_id, user)

                self._execution_service.add_finish_listener(cleanup, execution_id)
        except:
            LOGGER.exception('Failed to execute ' + job.get_log_name())

        self.schedule_job(job, job_path)

    def save_job(self, job: SchedulingJob):
        user = job.user
        script_name = job.script_name

        filename = file_utils.to_filename('%s_%s_%s.json' % (script_name, user.get_audit_name(), job.id))
        path = os.path.join(self._schedules_folder, filename)
        file_utils.write_file(
            path,
            json.dumps(job.as_serializable_dict(), indent=2))

        return path

    def _start_scheduler(self):
        def scheduler_loop():
            while not self.stopped:
                try:
                    self.scheduler.run(blocking=False)
                except:
                    LOGGER.exception('Failed to execute scheduled job')

                now = date_utils.now()
                sleep_delta = timedelta(minutes=1) - timedelta(microseconds=now.microsecond, seconds=now.second)
                _sleep(sleep_delta.total_seconds())

        self.scheduling_thread = threading.Thread(daemon=True, target=scheduler_loop)
        self.scheduling_thread.start()

    def _stop(self):
        self.stopped = True

        def stopper():
            pass

        # just schedule the next execution to exit thread immediately
        self.scheduler.enter(1, 0, stopper)


class InvalidUserException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class UnavailableScriptException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
