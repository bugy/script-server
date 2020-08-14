import calendar
import sys
import time
from datetime import datetime, timezone

MS_IN_SEC = 1000
MS_IN_MIN = 60 * MS_IN_SEC
MS_IN_HOUR = 60 * MS_IN_MIN
MS_IN_DAY = 24 * MS_IN_HOUR


def get_current_millis():
    return int(round(time.time() * 1000))


def to_millis(datetime):
    return int(round(datetime.timestamp() * 1000))


def ms_to_datetime(time_millis):
    return datetime.fromtimestamp(time_millis / 1000.0, tz=timezone.utc)


def sec_to_datetime(time_seconds):
    return datetime.fromtimestamp(time_seconds, tz=timezone.utc)


def astimezone(datetime_value, new_timezone):
    if (datetime_value.tzinfo is not None) or (sys.version_info >= (3, 6)):
        return datetime_value.astimezone(new_timezone)
    else:
        # From documentation: Naive datetime instances are assumed to represent local time
        timestamp = datetime_value.timestamp()
        local_tz_offset = datetime.fromtimestamp(timestamp) - datetime.utcfromtimestamp(timestamp)
        local_timezone = timezone(local_tz_offset)
        datetime_with_local_tz = datetime_value.replace(tzinfo=local_timezone)
        transformed = datetime_with_local_tz.astimezone(new_timezone)
        return transformed


def days_to_ms(days):
    return days * MS_IN_DAY


def ms_to_days(ms):
    return float(ms) / MS_IN_DAY


def parse_iso_datetime(date_str):
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)


def to_iso_string(datetime_value: datetime):
    if datetime_value.tzinfo is not None:
        datetime_value = datetime_value.astimezone(timezone.utc)

    return datetime_value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def is_past(dt: datetime):
    return now(tz=dt.tzinfo) > dt


def seconds_between(start: datetime, end: datetime):
    delta = end - start
    return delta.total_seconds()


def add_months(datetime_value: datetime, months):
    month = datetime_value.month - 1 + months
    year = datetime_value.year + month // 12
    month = month % 12 + 1
    day = min(datetime_value.day, calendar.monthrange(year, month)[1])
    return datetime_value.replace(year=year, month=month, day=day)


_mocked_now = None


def now(tz=timezone.utc):
    if _mocked_now is not None:
        return _mocked_now

    return datetime.now(tz)
