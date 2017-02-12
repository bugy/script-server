import urllib.request

import alerts.destination_base as destination_base


class HttpDestination(destination_base.Destination):
    url = None

    def __init__(self, params_dict):
        self.url = params_dict.get('url')

        if not self.url:
            raise Exception('"url" is compulsory parameter for email destination')

        if not self.url.strip().lower().startswith('http'):
            self.url = 'http://' + self.url.strip()

    def send(self, title, body):
        message = title + '\n' + body
        urlopen = urllib.request.urlopen(self.url, data=message.encode('utf-8'))
        urlopen.read()
        urlopen.close()

    def __str__(self, *args, **kwargs):
        return 'Web-hook at ' + self.url
