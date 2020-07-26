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
from utils import file_utils, date_utils

SCRIPT_NAME_KEY = 'script_name'
USER_KEY = 'user'
PARAM_VALUES_KEY = 'parameter_values'

JOB_SCHEDULE_KEY = 'schedule'

LOGGER = logging.getLogger('script_server.scheduling.schedule_service')

_sleep = time.sleep


def restore_jobs(schedules_folder):
    files = [file for file in os.listdir(schedules_folder) if file.endswith('.json')]

    job_dict = {}
    ids = []  # list of ALL ids, including broken configs

    for file in files:
        try:
            content = file_utils.read_file(os.path.join(schedules_folder, file))
            job_json = json.loads(content)
            ids.append(job_json['id'])

            job = scheduling_job.from_dict(job_json)

            job_dict[job.id] = job
        except:
            LOGGER.exception('Failed to parse schedule file: ' + file)

    return job_dict, ids


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
        self._scheduled_executions = jobs
        self._id_generator = IdGenerator(ids)
        self.stopped = False

        self.scheduler = sched.scheduler(timefunc=time.time)
        self._start_scheduler()

        for job in jobs.values():
            self.schedule_job(job)

    def create_job(self, script_name, parameter_values, incoming_schedule_config, user: User):
        if user is None:
            raise InvalidUserException('User id is missing')

        config_model = self._config_service.load_config_model(script_name, user, parameter_values)
        self.validate_script_config(config_model)

        schedule_config = read_schedule_config(incoming_schedule_config)

        if not schedule_config.repeatable and date_utils.is_past(schedule_config.start_datetime):
            raise InvalidScheduleException('Start date should be in the future')

        id = self._id_generator.next_id()

        job = SchedulingJob(id, user, schedule_config, script_name, parameter_values)

        self.save_job(job)

        self.schedule_job(job)

        return id

    @staticmethod
    def validate_script_config(config_model):
        if not config_model.schedulable:
            raise UnavailableScriptException(config_model.name + ' is not schedulable')

        for parameter in config_model.parameters:
            if parameter.secure:
                raise UnavailableScriptException(
                    'Script contains secure parameters (' + parameter.str_name() + '), this is not supported')

    def schedule_job(self, job: SchedulingJob):
        schedule = job.schedule

        if not schedule.repeatable and date_utils.is_past(schedule.start_datetime):
            return

        next_datetime = schedule.get_next_time()
        LOGGER.info(
            'Scheduling ' + job.get_log_name() + ' at ' + next_datetime.astimezone(tz=None).strftime('%H:%M, %d %B %Y'))

        self.scheduler.enterabs(next_datetime.timestamp(), 1, self._execute_job, (job,))

    def _execute_job(self, job: SchedulingJob):
        LOGGER.info('Executing ' + job.get_log_name())

        script_name = job.script_name
        parameter_values = job.parameter_values
        user = job.user

        try:
            config = self._config_service.load_config_model(script_name, user, parameter_values)
            self.validate_script_config(config)

            execution_id = self._execution_service.start_script(config, parameter_values, user.user_id,
                                                                user.audit_names)
            LOGGER.info('Started script #' + str(execution_id) + ' for ' + job.get_log_name())
        except:
            LOGGER.exception('Failed to execute ' + job.get_log_name())

        self.schedule_job(job)

    def save_job(self, job: SchedulingJob):
        user = job.user
        script_name = job.script_name

        filename = file_utils.to_filename('%s_%s_%s.json' % (script_name, user.get_audit_name(), job.id))
        file_utils.write_file(
            os.path.join(self._schedules_folder, filename),
            json.dumps(job.as_serializable_dict(), indent=2))

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
