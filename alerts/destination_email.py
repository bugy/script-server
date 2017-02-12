import os
import smtplib

import alerts.destination_base as destination_base


def split_addresses(addresses_string):
    if ',' in addresses_string:
        return addresses_string.split(',')

    if ';' in addresses_string:
        return addresses_string.split(';')

    return [addresses_string]


class EmailDestination(destination_base.Destination):
    from_address = None
    to_addresses = None
    server = None
    password = None

    def __init__(self, params_dict):
        self.from_address = params_dict.get('from')
        self.to_addresses = params_dict.get('to')
        self.server = params_dict.get('server')

        self.password = self.read_password(params_dict)
        self.to_addresses = split_addresses(self.to_addresses)

        if not self.from_address:
            raise Exception('"from" is compulsory parameter for email destination')

        if not self.to_addresses:
            raise Exception('"to" is compulsory parameter for email destination')

        if not self.server:
            raise Exception('"server" is compulsory parameter for email destination')

        if not self.password:
            raise Exception('"password" is compulsory parameter for email destination')

    @staticmethod
    def read_password(params_dict):
        password = params_dict.get('password')
        if password and password.startswith('$$'):
            env_password = os.environ[password[2:]]
            if env_password:
                password = env_password
        return password

    def send(self, title, body):
        message = 'Subject: {}\n\n{}'.format(title, body)

        server = smtplib.SMTP(self.server)
        server.ehlo()
        server.starttls()
        server.login(self.from_address, self.password)
        server.sendmail(self.from_address, self.to_addresses, message)
        server.quit()

    def __str__(self, *args, **kwargs):
        return 'mail to ' + str(self.to_addresses) + ' over ' + self.from_address
