import unittest
from datetime import datetime, timezone

from utils import date_utils


class TestScriptOutputLogging(unittest.TestCase):
    def test_astimezone_naive_after_dst(self):
        utc_datetime = datetime(2018, 6, 5, 12, 34, 56, tzinfo=timezone.utc)
        local_datetime = utc_datetime.astimezone(tz=None)
        naive_datetime = local_datetime.replace(tzinfo=None)

        transformed_datetime = date_utils.astimezone(naive_datetime, timezone.utc)
        self.assertEqual(utc_datetime, transformed_datetime)

    def test_astimezone_naive_before_dst(self):
        utc_datetime = datetime(2017, 1, 15, 20, 00, 00, tzinfo=timezone.utc)
        local_datetime = utc_datetime.astimezone(tz=None)
        naive_datetime = local_datetime.replace(tzinfo=None)

        transformed_datetime = date_utils.astimezone(naive_datetime, timezone.utc)
        self.assertEqual(utc_datetime, transformed_datetime)
