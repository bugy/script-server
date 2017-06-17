import smtplib

from alerts import destination_base
from model import model_helper


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
    login = None
    password = None
    auth_enabled = None
    tls = None

    def __init__(self, params_dict):
        self.from_address = params_dict.get('from')
        self.to_addresses = params_dict.get('to')
        self.server = params_dict.get('server')
        self.auth_enabled = params_dict.get('auth_enabled')
        self.login = params_dict.get('login')
        self.tls = params_dict.get('tls')

        self.password = self.read_password(params_dict)
        self.to_addresses = split_addresses(self.to_addresses)

        if not self.from_address:
            raise Exception('"from" is compulsory parameter for email destination')

        if not self.to_addresses:
            raise Exception('"to" is compulsory parameter for email destination')

        if not self.server:
            raise Exception('"server" is compulsory parameter for email destination')

        if self.auth_enabled is None:
            self.auth_enabled = self.password or self.login
        elif (self.auth_enabled == True) or (self.auth_enabled.lower() == 'true'):
            self.auth_enabled = True
        else:
            self.auth_enabled = False

        if self.auth_enabled and (not self.login):
            self.login = self.from_address

        if (self.tls is None) and ('gmail' in self.server):
            self.tls = True

    @staticmethod
    def read_password(params_dict):
        password = params_dict.get('password')
        password = model_helper.unwrap_conf_value(password)

        return password

    def send(self, title, body):
        message = 'Subject: {}\n\n{}'.format(title, body)

        server = smtplib.SMTP(self.server)
        server.ehlo()

        if self.tls:
            server.starttls()

        if self.auth_enabled:
            server.login(self.login, self.password)

        server.sendmail(self.from_address, self.to_addresses, message)
        server.quit()

    def __str__(self, *args, **kwargs):
        return 'mail to ' + '; '.join(self.to_addresses) + ' over ' + self.from_address
