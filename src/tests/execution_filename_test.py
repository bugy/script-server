import unittest

from execution.logging import LogNameCreator
from model.server_conf import LoggingConfig
from tests.test_utils import create_audit_names

_DATETIME = 1525595426234  # 08:30:25.234 06 May 2018


class TestLogNameCreator(unittest.TestCase):
    def test_default_format(self):
        filename = self.create_filename()
        self.assertEqual(filename, 'my_script_bugy_180506_083026.log')

    def test_custom_date_format(self):
        filename = self.create_filename(date_format='xx%y-%m-%d_%fxx')
        self.assertEqual(filename, 'my_script_bugy_xx18-05-06_234000xx.log')

    def test_custom_name_id_only(self):
        filename = self.create_filename(filename_pattern='$ID')
        self.assertEqual('12345.log', filename)

    def test_custom_name_with_all_audit_names(self):
        filename = self.create_filename(filename_pattern='$IP-$HOSTNAME-$USERNAME-$AUDIT_NAME',
                                        all_audit_names=create_audit_names(
                                            ip='192.168.2.3',
                                            auth_username='bugy',
                                            proxy_username='proxied_me',
                                            hostname='local-pc'))
        self.assertEqual('192.168.2.3-local-pc-bugy-bugy.log', filename)

    def test_custom_name_with_log_extension(self):
        filename = self.create_filename('$ID.log')
        self.assertEqual('12345.log', filename)

    def test_missing_hostname(self):
        filename = self.create_filename('$SCRIPT-$HOSTNAME')
        self.assertEqual('my_script-unknown-host.log', filename)

    def test_replace_whitespaces(self):
        filename = self.create_filename(date_format='%H %M %S',
                                        script_name='hello world',
                                        all_audit_names=create_audit_names(auth_username='a b'))
        self.assertEqual('hello_world_a_b_08_30_26.log', filename)

    @staticmethod
    def create_filename(filename_pattern=None,
                        date_format=None,
                        id=12345,
                        script_name='my_script',
                        datetime=_DATETIME,
                        all_audit_names=None,
                        custom_logging_config: LoggingConfig = None,
                        parameter_configs=None,
                        parameter_values=None):
        if all_audit_names is None:
            all_audit_names = create_audit_names(auth_username='bugy')

        if parameter_configs is None:
            parameter_configs = []
        if parameter_values is None:
            parameter_values = {}

        creator = LogNameCreator(filename_pattern, date_format)
        return creator.create_filename(
            id,
            all_audit_names,
            script_name,
            datetime,
            custom_logging_config,
            parameter_configs,
            parameter_values)
