import unittest
from datetime import datetime, timezone, timedelta

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


class TestParseIsoDatetime(unittest.TestCase):
    def test_parse_correct_time(self):
        parsed = date_utils.parse_iso_datetime('2020-07-10T15:30:59.123456Z')
        expected = datetime(2020, 7, 10, 15, 30, 59, 123456, timezone.utc)
        self.assertEqual(expected, parsed)

    def test_parse_wrong_time(self):
        self.assertRaisesRegex(
            ValueError,
            'does not match format',
            date_utils.parse_iso_datetime,
            '15:30:59 2020-07-10')


class TestToIsoString(unittest.TestCase):
    def test_utc_time(self):
        iso_string = date_utils.to_iso_string(datetime(2020, 7, 10, 15, 30, 59, 123456, timezone.utc))
        self.assertEqual('2020-07-10T15:30:59.123456Z', iso_string)

    def test_naive_time(self):
        iso_string = date_utils.to_iso_string(datetime(2020, 7, 10, 15, 30, 59, 123456))
        self.assertEqual('2020-07-10T15:30:59.123456Z', iso_string)

    def test_local_time(self):
        iso_string = date_utils.to_iso_string(datetime(2020, 7, 10, 15, 30, 59, 123456, timezone(timedelta(hours=1))))
        self.assertEqual('2020-07-10T14:30:59.123456Z', iso_string)


class TestIsPast(unittest.TestCase):
    def test_when_past_naive(self):
        value = datetime(2020, 7, 10, 15, 30, 59, 123456)

        self.assertTrue(date_utils.is_past(value))

    def test_when_past_utc(self):
        value = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)

        self.assertTrue(date_utils.is_past(value))

    def test_when_future_naive(self):
        value = datetime(2030, 7, 10, 15, 30, 59, 123456)

        self.assertFalse(date_utils.is_past(value))

    def test_when_future_utc(self):
        value = datetime(2030, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)

        self.assertFalse(date_utils.is_past(value))

    def test_when_now(self):
        value = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)

        date_utils._mocked_now = value

        self.assertFalse(date_utils.is_past(value))

    def tearDown(self) -> None:
        date_utils._mocked_now = None


class TestSecondsBetween(unittest.TestCase):
    def test_small_positive_delta(self):
        start = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        end = datetime(2020, 7, 10, 15, 33, 12, 123456, tzinfo=timezone.utc)

        seconds = date_utils.seconds_between(start, end)
        self.assertEqual(133, seconds)

    def test_small_negative_delta(self):
        start = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        end = datetime(2020, 7, 10, 15, 30, 13, 123456, tzinfo=timezone.utc)

        seconds = date_utils.seconds_between(start, end)
        self.assertEqual(-46, seconds)

    def test_large_positive_delta(self):
        start = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        end = datetime(2021, 2, 15, 17, 33, 12, 123456, tzinfo=timezone.utc)

        seconds = date_utils.seconds_between(start, end)
        self.assertEqual(19015333, seconds)

    def test_large_negative_delta(self):
        start = datetime(2020, 7, 10, 15, 30, 13, 123456, tzinfo=timezone.utc)
        end = datetime(2019, 11, 29, 9, 30, 59, 123456, tzinfo=timezone.utc)

        seconds = date_utils.seconds_between(start, end)
        self.assertEqual(-19375154, seconds)

    def test_delta_with_microseconds(self):
        start = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        end = datetime(2020, 7, 10, 15, 33, 12, 876543, tzinfo=timezone.utc)

        seconds = date_utils.seconds_between(start, end)
        self.assertEqual(133.753087, seconds)


class TestAddMonths(unittest.TestCase):
    def test_add_one_month(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 1)
        expected = datetime(2020, 8, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_4_months(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 4)
        expected = datetime(2020, 11, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_roll_next_year(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 6)
        expected = datetime(2021, 1, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_roll_multiple_years(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 33)
        expected = datetime(2023, 4, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_last_day_when_next_shorter(self):
        original = datetime(2020, 7, 31, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 2)
        expected = datetime(2020, 9, 30, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_last_day_when_next_same(self):
        original = datetime(2020, 7, 31, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 1)
        expected = datetime(2020, 8, 31, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_last_day_when_next_longer(self):
        original = datetime(2020, 6, 30, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 2)
        expected = datetime(2020, 8, 30, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_last_day_when_next_february(self):
        original = datetime(2020, 7, 30, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 7)
        expected = datetime(2021, 2, 28, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_add_months_to_last_day_when_next_leap_february(self):
        original = datetime(2019, 7, 30, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, 7)
        expected = datetime(2020, 2, 29, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_subtract_one_month(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, -1)
        expected = datetime(2020, 6, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)

    def test_subtract_months_to_prev_year(self):
        original = datetime(2020, 7, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        added = date_utils.add_months(original, -10)
        expected = datetime(2019, 9, 10, 15, 30, 59, 123456, tzinfo=timezone.utc)
        self.assertEqual(expected, added)
