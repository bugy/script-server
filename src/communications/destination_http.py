import json
from copy import copy

import requests

import communications.destination_base as destination_base
from model.model_helper import read_obligatory


def _create_communicator(params_dict):
    return HttpCommunicator(params_dict)


class HttpDestination(destination_base.Destination):
    def __init__(self, params_dict):
        self._communicator = _create_communicator(params_dict)

    def send(self, title, body, files=None):
        content_type = None

        new_body = copy(body)

        if files:
            if not isinstance(body, dict):
                raise Exception('Files are supported only for JSON body, was ' + repr(body))

            body_files = {}
            for file in files:
                body_files[file.filename] = file.content
            new_body['files'] = body_files

        if isinstance(body, dict):
            content_type = 'application/json'
            new_body = json.dumps(new_body)

        self._communicator.send(new_body, content_type=content_type)

    def __str__(self, *args, **kwargs):
        return type(self).__name__ + ' for ' + str(self._communicator)


class HttpCommunicator:
    def __init__(self, params_dict):
        self.url = read_obligatory(params_dict, 'url', ' for HTTP callback')

        if not self.url.strip().lower().startswith('http'):
            self.url = 'http://' + self.url.strip()

    def send(self, body, content_type=None):
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type

        requests.post(self.url, data=body, headers=headers)

    def __str__(self, *args, **kwargs):
        return 'Web-hook at ' + self.url
