import random
import unittest
from datetime import datetime, timezone

from execution.logging import HistoryEntry
from model.external_model import to_short_execution_log, to_long_execution_log, server_conf_to_external, \
    parse_external_schedule
from model.server_conf import ServerConfig


class TestHistoryEntry(unittest.TestCase):
    def test_simple_short_entry(self):
        entry = self._create_history_entry(
            'id1',
            user_name='my user',
            script_name='Destroy world',
            exit_code='5'
        )

        translated_entries = to_short_execution_log([entry])
        self.assertEqual(1, len(translated_entries))
        self._validate_translated_entry(
            translated_entries[0],
            'id1',
            user='my user',
            script_name='Destroy world',
            exit_code='5'
        )

    def test_start_time_translation(self):
        entry = self._create_history_entry(
            'id1',
            start_time=datetime.strptime('18:25:22+0230_2018_04_03', "%H:%M:%S%z_%Y_%m_%d")
        )

        translated_entries = to_short_execution_log([entry])
        self._validate_translated_entry(
            translated_entries[0],
            'id1',
            start_time_string='2018-04-03T15:55:22+00:00'
        )

    def test_start_time_without_timezone(self):
        start_time_local = datetime(2018, 4, 5, 12, 34, 56, tzinfo=timezone.utc).astimezone(tz=None)
        start_time_naive = start_time_local.replace(tzinfo=None)
        entry = self._create_history_entry(
            'id1',
            start_time=start_time_naive
        )

        translated_entries = to_short_execution_log([entry])

        self._validate_translated_entry(
            translated_entries[0],
            'id1',
            start_time_string=start_time_local.astimezone(tz=timezone.utc).isoformat()
        )

    def test_missing_start_time(self):
        entry = self._create_history_entry('id1')
        entry.start_time = None
        translated_entries = to_short_execution_log([entry])

        self.assertIn('startTime', translated_entries[0])
        self.assertIsNone(translated_entries[0]['startTime'])

    def test_running_status(self):
        entry = self._create_history_entry('id1')
        translated_entries = to_short_execution_log([entry], ['id0', 'id1', 'id2'])
        self._validate_translated_entry(translated_entries[0], 'id1', status='running')

    def test_multiple_short_entries(self):
        entry1 = self._create_history_entry('id1', user_name='my user', )
        entry2 = self._create_history_entry('id2', script_name='Destroy world', )
        entry3 = self._create_history_entry('id3', exit_code='13')

        translated_entries = to_short_execution_log([entry1, entry2, entry3])
        self.assertEqual(3, len(translated_entries))
        self._validate_translated_entry(translated_entries[0], 'id1', user='my user')
        self._validate_translated_entry(translated_entries[1], 'id2', script_name='Destroy world')
        self._validate_translated_entry(translated_entries[2], 'id3', exit_code='13')

    def test_long_history_entry(self):
        entry = self._create_history_entry('id1', command='ping localhost')
        long_entry = to_long_execution_log(entry, 'log text\nend', True)

        self._validate_translated_entry(
            long_entry,
            'id1',
            log='log text\nend',
            status='running',
            command='ping localhost')

    def _create_history_entry(self,
                              id,
                              user_name='userX',
                              user_id=None,
                              script_name='my_script',
                              command='cmd',
                              start_time=None,
                              exit_code='0'):
        if id is None:
            id = str(self.random_instance.randint(0, 10000000))

        if start_time is None:
            start_time = datetime.now(timezone.utc)

        if user_id is None:
            user_id = user_name

        entry = HistoryEntry()
        entry.id = id
        entry.user_name = user_name
        entry.user_id = user_id
        entry.start_time = start_time
        entry.script_name = script_name
        entry.command = command
        entry.exit_code = exit_code

        return entry

    def _validate_translated_entry(self,
                                   entry,
                                   id,
                                   user='userX',
                                   script_name='my_script',
                                   status='finished',
                                   command=None,
                                   start_time_string=None,
                                   exit_code='0',
                                   log=None):
        self.assertEqual(entry.get('id'), id)
        self.assertEqual(entry.get('user'), user)
        self.assertEqual(entry.get('script'), script_name)
        self.assertEqual(entry.get('status'), status)
        self.assertEqual(entry.get('command'), command)
        self.assertEqual(entry.get('exitCode'), exit_code)
        self.assertEqual(entry.get('log'), log)

        if start_time_string is not None:
            self.assertEqual(entry.get('startTime'), start_time_string)

    def setUp(self):
        self.random_instance = random.seed(a=123)


class TestServerConf(unittest.TestCase):
    def test_full_config(self):
        config = ServerConfig()
        config.title = 'test title'
        config.enable_script_titles = False

        external_config = server_conf_to_external(config, '1.14.0')
        self.assertEqual('test title', external_config.get('title'))
        self.assertIs(False, external_config.get('enableScriptTitles'))
        self.assertIs('1.14.0', external_config.get('version'))

    def test_config_with_none_values(self):
        config = ServerConfig()
        config.title = None
        config.enable_script_titles = None

        external_config = server_conf_to_external(config, None)
        self.assertIsNone(external_config.get('title'))
        self.assertIsNone(external_config.get('enableScriptTitles'))
        self.assertIsNone(external_config.get('version'))


class TestParseExternalSchedule(unittest.TestCase):
    def test_parse_full_config(self):
        parsed = parse_external_schedule(
            {'repeatable': False, 'startDatetime': '2020-12-30', 'repeatUnit': 'days', 'repeatPeriod': 5,
             'weekDays': ['monday', 'Tuesday']})

        self.assertDictEqual({
            'repeatable': False,
            'start_datetime': '2020-12-30',
            'repeat_unit': 'days',
            'repeat_period': 5,
            'weekdays': ['monday', 'Tuesday']},
            parsed)

    def test_parse_partial_config(self):
        parsed = parse_external_schedule(
            {'repeatable': False, 'startDatetime': '2020-12-30'})

        self.assertDictEqual({
            'repeatable': False,
            'start_datetime': '2020-12-30',
            'repeat_unit': None,
            'repeat_period': None,
            'weekdays': None},
            parsed)

    def test_parse_unknown_field(self):
        parsed = parse_external_schedule(
            {'repeatable': False,
             'startDatetime': '2020-12-30',
             'anotherField': 'abc'})

        self.assertDictEqual({
            'repeatable': False,
            'start_datetime': '2020-12-30',
            'repeat_unit': None,
            'repeat_period': None,
            'weekdays': None}, parsed)
