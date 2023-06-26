from datetime import timezone, timedelta, datetime

from model import model_helper
from utils import date_utils
from utils.string_utils import is_blank

ALLOWED_WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _read_datetime(incoming_schedule_config, key):
    datetime_value = model_helper.read_datetime_from_config(key, incoming_schedule_config)
    if datetime_value is None:
        raise InvalidScheduleException('%1 is required', key)
    return datetime_value

def _read_repeat_unit(incoming_schedule_config):
    repeat_unit = incoming_schedule_config.get('repeat_unit')
    if is_blank(repeat_unit):
        raise InvalidScheduleException('repeat_unit is required for repeatable schedule')

    if repeat_unit.lower() not in ['minutes', 'hours', 'days', 'weeks', 'months']:
        raise InvalidScheduleException('repeat_unit should be one of: minutes, hours, days, weeks, months')

    return repeat_unit.lower()


def _read_repeat_period(incoming_schedule_config):
    period = model_helper.read_int_from_config('repeat_period', incoming_schedule_config, default=1)
    if period <= 0:
        raise InvalidScheduleException('repeat_period should be > 0')
    return period


def read_repeatable_flag(incoming_schedule_config):
    repeatable = model_helper.read_bool_from_config('repeatable', incoming_schedule_config)
    if repeatable is None:
        raise InvalidScheduleException('Missing "repeatable" field')
    return repeatable


def read_weekdays(incoming_schedule_config):
    weekdays = model_helper.read_list(incoming_schedule_config, 'weekdays')
    if not weekdays:
        raise InvalidScheduleException('At least one weekday should be specified')
    weekdays = [day.lower().strip() for day in weekdays]
    for day in weekdays:
        if day not in ALLOWED_WEEKDAYS:
            raise InvalidScheduleException('Unknown weekday: ' + day)
    return sorted(weekdays, key=lambda x: ALLOWED_WEEKDAYS.index(x))


def read_schedule_config(incoming_schedule_config):
    repeatable = read_repeatable_flag(incoming_schedule_config)
    start_datetime = _read_datetime(incoming_schedule_config, 'start_datetime')

    prepared_schedule_config = ScheduleConfig(repeatable, start_datetime)
    if repeatable:

        end_option = incoming_schedule_config.get('end_option')
        prepared_schedule_config.end_option = end_option
        if end_option == 'on':
            prepared_schedule_config.end_arg = _read_datetime(incoming_schedule_config, 'end_arg')
        elif end_option == 'after':
            prepared_schedule_config.end_arg = model_helper.read_int_from_config('end_arg', incoming_schedule_config)
        else:
            prepared_schedule_config.end_option = 'never'

        prepared_schedule_config.repeat_unit = _read_repeat_unit(incoming_schedule_config)
        prepared_schedule_config.repeat_period = _read_repeat_period(incoming_schedule_config)

        if prepared_schedule_config.repeat_unit == 'weeks':
            prepared_schedule_config.weekdays = read_weekdays(incoming_schedule_config)

    return prepared_schedule_config


class ScheduleConfig:

    def __init__(self, repeatable, start_datetime) -> None:
        self.repeatable = repeatable
        self.start_datetime = start_datetime  # type: datetime
        self.end_option = None
        self.end_arg = None
        self.repeat_unit = None
        self.repeat_period = None
        self.weekdays = None

    def as_serializable_dict(self):
        result = {
            'repeatable': self.repeatable,
            'start_datetime': date_utils.to_iso_string(self.start_datetime),
        }

        if self.end_option == 'on':
            result['end_option'] = self.end_option
            result['end_arg'] = date_utils.to_iso_string(self.end_arg)
        elif self.end_option == 'after':
            result['end_option'] = self.end_option
            result['end_arg'] = self.end_arg

        if self.repeat_unit is not None:
            result['repeat_unit'] = self.repeat_unit

        if self.repeat_period is not None:
            result['repeat_period'] = self.repeat_period

        if self.weekdays is not None:
            result['weekdays'] = self.weekdays

        return result

    def get_next_time(self):
        if not self.repeatable:
            return self.start_datetime

        if self.repeat_unit == 'minutes':
            next_time_func = lambda start, iteration_index: \
                start + timedelta(minutes=self.repeat_period * iteration_index)
            get_initial_multiplier = lambda start: \
                ((now - start).seconds // 60 + (now - start).days * 1440) \
                // self.repeat_period
        elif self.repeat_unit == 'hours':
            next_time_func = lambda start, iteration_index: start + timedelta(
                hours=self.repeat_period * iteration_index)

            get_initial_multiplier = lambda start: \
                ((now - start).seconds // 3600 + (now - start).days * 24) \
                // self.repeat_period
        elif self.repeat_unit == 'days':
            next_time_func = lambda start, iteration_index: start + timedelta(days=self.repeat_period * iteration_index)
            get_initial_multiplier = lambda start: (now - start).days // self.repeat_period
        elif self.repeat_unit == 'months':
            next_time_func = lambda start, iteration_index: date_utils.add_months(start,
                                                                                  self.repeat_period * iteration_index)
            get_initial_multiplier = lambda start: (now - start).days // 28 // self.repeat_period
        elif self.repeat_unit == 'weeks':
            start_weekday = self.start_datetime.weekday()
            offset = 0
            for weekday in self.weekdays:
                index = ALLOWED_WEEKDAYS.index(weekday)
                if index < start_weekday:
                    offset += 1

            def next_weekday(start: datetime, iteration_index):
                weeks_multiplier = (iteration_index + offset) // len(self.weekdays)
                next_weekday_index = (iteration_index + offset) % len(self.weekdays)
                next_weekday_name = self.weekdays[next_weekday_index]
                next_weekday = ALLOWED_WEEKDAYS.index(next_weekday_name)

                return start \
                       + timedelta(weeks=self.repeat_period * weeks_multiplier) \
                       + timedelta(days=(next_weekday - start.weekday()))

            next_time_func = next_weekday

            get_initial_multiplier = lambda start: (now - start).days // 7 // self.repeat_period * len(
                self.weekdays) - 1
        else:
            raise Exception('Unknown unit: ' + repr(self.repeat_unit))

        now = date_utils.now(tz=timezone.utc)
        max_iterations = 10000
        initial_multiplier = max(0, get_initial_multiplier(self.start_datetime))
        i = 0
        while True:
            resolved_time = next_time_func(self.start_datetime, i + initial_multiplier)
            if resolved_time >= now:
                return resolved_time

            i += 1
            if i > max_iterations:
                raise Exception('Endless loop in calc next time')


class InvalidScheduleException(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
