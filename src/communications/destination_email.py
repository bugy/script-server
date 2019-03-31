import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from communications import destination_base
from model import model_helper
from model.model_helper import read_bool_from_config


def split_addresses(addresses_string):
    if ',' in addresses_string:
        return addresses_string.split(',')

    if ';' in addresses_string:
        return addresses_string.split(';')

    return [addresses_string]


def _create_communicator(config):
    return EmailCommunicator(config)


def _body_dict_to_message(body_dict):
    result = ''

    for key, value in body_dict.items():
        if result:
            result += '\n'
        result += key + ': ' + str(value)

    return result


class EmailDestination(destination_base.Destination):

    def __init__(self, config) -> None:
        super().__init__()

        self._communicator = _create_communicator(config)

    def send(self, title, body, files=None):
        if isinstance(body, dict):
            body = _body_dict_to_message(body)

        self._communicator.send(title, body, files)


class EmailCommunicator:
    def __init__(self, params_dict):
        self.from_address = params_dict.get('from')
        self.to_addresses = params_dict.get('to')
        self.server = params_dict.get('server')
        self.auth_enabled = read_bool_from_config('auth_enabled', params_dict)
        self.login = params_dict.get('login')
        self.tls = read_bool_from_config('tls', params_dict)

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

        if self.auth_enabled and (not self.login):
            self.login = self.from_address

        if (self.tls is None) and ('gmail' in self.server):
            self.tls = True

    @staticmethod
    def read_password(params_dict):
        password = params_dict.get('password')
        password = model_helper.resolve_env_vars(password, full_match=True)

        return password

    def send(self, title, body, files=None):
        message = MIMEMultipart()
        message['From'] = self.from_address
        message['To'] = ','.join(self.to_addresses)
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = title

        message.attach(MIMEText(body))

        server = smtplib.SMTP(self.server)
        server.ehlo()

        if self.tls:
            server.starttls()

        if self.auth_enabled:
            server.login(self.login, self.password)

        if files:
            for file in files:
                filename = file.filename
                part = MIMEApplication(file.content, Name=filename)
                part['Content-Disposition'] = 'attachment; filename="%s"' % filename
                message.attach(part)

        server.sendmail(self.from_address, self.to_addresses, message.as_string())
        server.quit()

    def __str__(self, *args, **kwargs):
        return 'mail to ' + '; '.join(self.to_addresses) + ' over ' + self.from_address
