from auth import user
from auth.user import User
from scheduling import schedule_config
from scheduling.schedule_config import ScheduleConfig


class SchedulingJob:
    def __init__(self, id, user, schedule_config, script_name, parameter_values) -> None:
        self.id = str(id)
        self.user = user  # type: User
        self.schedule = schedule_config  # type: ScheduleConfig
        self.script_name = script_name
        self.parameter_values = parameter_values  # type: dict

    def as_serializable_dict(self):
        return {
            'id': self.id,
            'user': self.user.as_serializable_dict(),
            'schedule': self.schedule.as_serializable_dict(),
            'script_name': self.script_name,
            'parameter_values': self.parameter_values
        }

    def get_log_name(self):
        return 'Job#' + str(self.id) + '-' + self.script_name


def from_dict(job_as_dict):
    id = job_as_dict['id']
    parsed_user = user.from_serialized_dict(job_as_dict['user'])
    schedule = schedule_config.read_schedule_config(job_as_dict['schedule'])
    script_name = job_as_dict['script_name']
    parameter_values = job_as_dict['parameter_values']

    return SchedulingJob(id, parsed_user, schedule, script_name, parameter_values)
