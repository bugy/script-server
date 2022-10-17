#!/usr/bin/env python3
import functools
import json
import logging.config
import uuid
from concurrent.futures.thread import ThreadPoolExecutor

import tornado.concurrent
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen

from auth.user import User
from config.config_service import ConfigNotAllowedException, BadConfigFileException
from model import external_model
from model.external_model import parameter_to_external
from model.model_helper import read_bool
from model.script_config import ConfigModel
from web.web_auth_utils import check_authorization
from web.web_utils import wrap_to_server_event, inject_user

LOGGER = logging.getLogger('web.script_config_socket')

active_config_models = {}


class ScriptConfigSocket(tornado.websocket.WebSocketHandler):
    user: User
    config_mode: ConfigModel

    # noinspection PyTypeChecker
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.config_model = None
        self.config_name = None
        self.user = None
        self.config_id = str(uuid.uuid4())

        self.init_with_values = read_bool(self.get_query_argument('initWithValues', default='false'))

        self.parameters_listener = self._create_parameters_listener()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='-model-' + self.config_id)
        self._parameter_events_queue = []
        self._latest_client_state_version = None

    @check_authorization
    @inject_user
    @gen.coroutine
    def open(self, user, config_name):
        self.config_name = config_name
        self.user = user
        self.ioloop = tornado.ioloop.IOLoop.current()

        if self.init_with_values:
            return

        yield self._prepare_and_send_model(event_type='initialConfig')

    @gen.coroutine
    def on_message(self, text):
        try:
            message = json.loads(text)

            type = message.get('event')
            data = message.get('data')

            if type == 'parameterValue':
                set_parameter_func = functools.partial(
                    self._set_parameter_value,
                    data.get('parameter'),
                    data.get('value'),
                    data.get('clientStateVersion'))

                self._start_task(set_parameter_func)
                return
            elif type == 'reloadModelValues':
                parameter_values = data.get('parameterValues')
                external_id = data.get('clientModelId')

                yield self._prepare_and_send_model(parameter_values=parameter_values,
                                                   external_id=external_id,
                                                   event_type='reloadedConfig',
                                                   client_state_version=data.get('clientStateVersion'))
                return
            elif type == 'initialValues':
                if not self.init_with_values:
                    logging.warning('Received initial values, but not expected. Ignoring')
                    return
                if self.config_model:
                    logging.warning('Received initial values, but model is already initialized. Ignoring')
                    return
                parameter_values = data.get('parameterValues')

                yield self._prepare_and_send_model(parameter_values=parameter_values,
                                                   event_type='initialConfig')
                return

            LOGGER.warning('Unknown message received in ScriptConfigSocket: ' + text)
        except:
            LOGGER.exception('Failed to process message ' + text)

    def _start_task(self, func):
        future = tornado.ioloop.IOLoop.current().run_in_executor(
            executor=self._executor,
            func=func)

        return future

    def _set_parameter_value(self, parameter, value, client_state_version):
        self._latest_client_state_version = client_state_version
        self.config_model.set_param_value(parameter, value)
        self._send_parameter_event('clientStateVersionAccepted', {})

    def on_close(self):
        if self.config_id in active_config_models:
            del active_config_models[self.config_id]

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.ioloop.add_callback(self.write_message, message)

    def _send_parameter_changed(self, parameter):
        external_param = parameter_to_external(parameter)
        if external_param is None:
            return

        self._send_parameter_event('parameterChanged', external_param)

    def _send_parameter_event(self, event_type, data):
        event = self._create_event(event_type, data)

        self.safe_write(event)

    def _subscribe_on_parameter(self, parameter):
        parameter.subscribe(lambda prop, old, new: self._send_parameter_changed(parameter))

    def _set_model(self, config_model: ConfigModel):
        if self.config_model is not None:
            self.config_model.parameters.unsubscribe(self.parameters_listener)

        self.config_model = config_model
        self.config_model.parameters.subscribe(self.parameters_listener)

        active_config_models[self.config_id] = {'model': self.config_model, 'user_id': self.user.user_id}

        for parameter in self.config_model.parameters:
            self._subscribe_on_parameter(parameter)

    def _create_parameters_listener(self):
        socket = self

        class ParameterListener:
            def on_add(self, parameter, index):
                external_parameter = parameter_to_external(parameter)
                if external_parameter is not None:
                    socket._send_parameter_event('parameterAdded', external_parameter)
                    socket._subscribe_on_parameter(parameter)

            def on_remove(self, parameter):
                external_parameter = parameter_to_external(parameter)
                if external_parameter is not None:
                    socket._send_parameter_event('parameterRemoved', {'parameterName': external_parameter['name']})

        return ParameterListener()

    @gen.coroutine
    def _prepare_model(self, config_name, user, parameter_values=None, skip_invalid_parameters=False) -> ConfigModel:
        try:
            socket = self

            def load_model():
                model = socket.application.config_service.load_config_model(config_name, user,
                                                                            parameter_values=parameter_values,
                                                                            skip_invalid_parameters=skip_invalid_parameters)

                socket._parameter_events_queue.clear()
                return model

            config_model = yield (self._start_task(load_model))

        except ConfigNotAllowedException:
            self.close(code=403, reason='Access to the script is denied')
            return None
        except BadConfigFileException:
            self.close(code=422, reason=BadConfigFileException.VERBOSE_ERROR)
            return None
        except Exception:
            message = 'Failed to load script config ' + config_name
            LOGGER.exception(message)
            self.close(code=500, reason=message)
            return None

        if not config_model:
            self.close(code=404, reason='Could not find a script by name')
            return None

        raise gen.Return(config_model)

    @gen.coroutine
    def _prepare_and_send_model(self, *, parameter_values=None, external_id=None, event_type,
                                client_state_version=None):
        config_model = yield self._prepare_model(self.config_name,
                                                 self.user,
                                                 parameter_values,
                                                 skip_invalid_parameters=True)
        if not config_model:
            return
        if client_state_version:
            self._latest_client_state_version = client_state_version

        self._set_model(config_model)

        new_config = external_model.config_to_external(config_model, self.config_id, external_id)
        self.safe_write(self._create_event(event_type, new_config))

    def _create_event(self, event_type, data):
        data['clientStateVersion'] = self._latest_client_state_version
        return wrap_to_server_event(event_type=event_type, data=data)
