import time
from datetime import datetime, timezone


def get_current_millis():
    return int(round(time.time() * 1000))


def to_millis(datetime):
    return int(round(datetime.timestamp() * 1000))


def ms_to_datetime(time_millis):
    return datetime.fromtimestamp(time_millis // 1000.0, tz=timezone.utc)


def sec_to_datetime(time_seconds):
    return datetime.fromtimestamp(time_seconds, tz=timezone.utc)
