import requests

import communications.destination_base as destination_base


class HttpDestination(destination_base.Destination):
    def __init__(self, params_dict):
        self.url = params_dict.get('url')

        if not self.url:
            raise Exception('"url" is compulsory parameter for email destination')

        if not self.url.strip().lower().startswith('http'):
            self.url = 'http://' + self.url.strip()

    def send(self, title, body, logs=None):
        message = title + '\n' + body
        data = {'message': message.encode('utf-8')}

        files = {}
        if logs:
            files['log'] = ('log.txt', logs)

        requests.post(self.url, data=data, files=files)

    def __str__(self, *args, **kwargs):
        return 'Web-hook at ' + self.url
