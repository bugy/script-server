import json
from datetime import datetime, timezone
from unittest import TestCase

from auth.user import User
from scheduling.schedule_config import ScheduleConfig
from scheduling.scheduling_job import SchedulingJob, from_dict
from utils import audit_utils


class TestSchedulingJob(TestCase):
    def test_serialize_deserialize(self):
        user = User('user-X', {audit_utils.AUTH_USERNAME: 'user-X', audit_utils.HOSTNAME: 'localhost'})
        schedule_config = ScheduleConfig(True, start_datetime=datetime.now(tz=timezone.utc))
        schedule_config.repeat_unit = 'weeks'
        schedule_config.repeat_period = 3
        schedule_config.weekdays = ['monday', 'wednesday']
        parameter_values = {'p1': 9, 'p2': ['A', 'C']}

        job = SchedulingJob(123, user, schedule_config, 'my_script', parameter_values)

        serialized = json.dumps(job.as_serializable_dict())
        restored_job = from_dict(json.loads(serialized))

        self.assertEqual(job.id, restored_job.id)
        self.assertEqual(job.script_name, restored_job.script_name)
        self.assertEqual(job.parameter_values, restored_job.parameter_values)

        self.assertEqual(job.user.user_id, restored_job.user.user_id)
        self.assertEqual(job.user.audit_names, restored_job.user.audit_names)

        self.assertEqual(job.schedule.repeatable, restored_job.schedule.repeatable)
        self.assertEqual(job.schedule.start_datetime, restored_job.schedule.start_datetime)
        self.assertEqual(job.schedule.repeat_period, restored_job.schedule.repeat_period)
        self.assertEqual(job.schedule.repeat_unit, restored_job.schedule.repeat_unit)
        self.assertEqual(job.schedule.weekdays, restored_job.schedule.weekdays)
