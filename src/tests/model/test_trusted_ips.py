from unittest import TestCase

from parameterized import parameterized

from model.trusted_ips import TrustedIpValidator


class TestTrustedIpValidator(TestCase):
    @parameterized.expand([
        (['192.168.0.15'], '192.168.0.15', True),
        (['192.168.0.0'], '192.168.0.15', False),
        (['192.168.0.1'], '192.168.0.15', False),
        (['127.0.0.1'], '127.0.0.1', True),
        (['::1'], '::1', True),
        (['192.168.0.15/32'], '192.168.0.15', True),
        (['192.168.0.16/32'], '192.168.0.15', False),
        (['192.168.0.14/31'], '192.168.0.15', True),
        (['192.168.0.16/31'], '192.168.0.15', False),
        (['192.168.0.0/28'], '192.168.0.15', True),
        (['192.168.0.0/28'], '192.168.0.15', True),
        (['192.168.0.0/28'], '192.168.0.16', False),
        (['192.168.0.16/28'], '192.168.0.15', False),
        (['192.168.0.16/28'], '192.168.0.16', True),
        (['192.168.0.0/24'], '192.168.0.16', True),
        (['192.168.0.0/16'], '192.168.32.127', True),
    ])
    def test_is_trusted(self, configured_ips, user_ip, expected_result):
        validator = TrustedIpValidator(configured_ips)
        trusted = validator.is_trusted(user_ip)
        self.assertEqual(expected_result, trusted, user_ip + ' is trusted=' + str(trusted)
                         + ' but should be ' + str(expected_result) + ' for ' + str(configured_ips))
