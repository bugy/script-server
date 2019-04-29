#!/usr/bin/env python3
import json
import logging.config
import os
import signal
import ssl
import time
import urllib
import uuid
from itertools import chain
from urllib.parse import urlencode
from urllib.parse import urlparse

import tornado.concurrent
import tornado.escape
import tornado.httpserver as httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from auth.identification import AuthBasedIdentification, IpBasedIdentification
from auth.tornado_auth import TornadoAuth
from auth.user import User
from communications.alerts_service import AlertsService
from config.config_service import ConfigService, ConfigNotAllowedException
from execution.execution_service import ExecutionService
from execution.logging import ExecutionLoggingService
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from model import external_model
from model.external_model import to_short_execution_log, to_long_execution_log, parameter_to_external
from model.model_helper import is_empty
from model.parameter_config import WrongParameterUsageException
from model.script_config import InvalidValueException, ParameterNotFoundException
from model.server_conf import ServerConfig
from utils import audit_utils, tornado_utils
from utils import file_utils as file_utils
from utils.audit_utils import get_audit_name_from_request
from utils.tornado_utils import respond_error, redirect_relative
from web.streaming_form_reader import StreamingFormReader

BYTES_IN_MB = 1024 * 1024

LOGGER = logging.getLogger('web_server')

active_config_models = {}


def is_allowed_during_login(request_path, login_url, request_handler):
    if request_handler.request.method != 'GET':
        return False

    if request_path == '/favicon.ico':
        return True

    if request_path == login_url:
        return True

    login_resources = ['/login.js',
                       '/login.js.map',
                       '/css/index.css',
                       '/login-deps.css',
                       '/login-deps.css.map',
                       '/fonts/roboto-latin-500.woff2',
                       '/fonts/roboto-latin-500.woff',
                       '/fonts/roboto-latin-400.woff2',
                       '/fonts/roboto-latin-400.woff',
                       '/images/titleBackground.jpg',
                       '/images/g-logo-plain.png',
                       '/images/g-logo-plain-pressed.png']

    if request_path not in login_resources:
        return False

    referer = request_handler.request.headers.get('Referer')
    if referer:
        referer = urlparse(referer).path
    else:
        return False

    allowed_referrers = [login_url, '/login-deps.css', '/css/index.css']
    for allowed_referrer in allowed_referrers:
        if referer.endswith(allowed_referrer):
            return True


# In case of REST requests we don't redirect explicitly, but reply with Unauthorized code.
# Client application should provide redirection in the way it likes
def check_authorization(func):
    def wrapper(self, *args, **kwargs):
        auth = self.application.auth
        authorizer = self.application.authorizer

        authenticated = auth.is_authenticated(self)
        access_allowed = authenticated and authorizer.is_allowed_in_app(_identify_user(self))

        if authenticated and (not access_allowed):
            user = _identify_user(self)
            LOGGER.warning('User ' + user + ' is not allowed')
            code = 403
            message = 'Access denied. Please contact system administrator'
            if isinstance(self, tornado.websocket.WebSocketHandler):
                self.close(code=code, reason=message)
            else:
                raise tornado.web.HTTPError(code, message)

        login_url = self.get_login_url()
        request_path = self.request.path

        login_resource = is_allowed_during_login(request_path, login_url, self)
        if (authenticated and access_allowed) or login_resource:
            return func(self, *args, **kwargs)

        if not isinstance(self, tornado.web.StaticFileHandler):
            raise tornado.web.HTTPError(401, 'Not authenticated')

        login_url += "?" + urlencode(dict(next=request_path))

        redirect_relative(login_url, self)

        return

    return wrapper


def inject_user(func):
    def wrapper(self, *args, **kwargs):
        user_id = _identify_user(self)
        audit_names = audit_utils.get_all_audit_names(self)

        user = User(user_id, audit_names)

        new_args = chain([user], args)
        return func(self, *new_args, **kwargs)

    return wrapper


def requires_admin_rights(func):
    def wrapper(self, *args, **kwargs):
        if not has_admin_rights(self):
            user_id = _identify_user(self)
            LOGGER.warning('User %s (%s) tried to access admin REST service %s',
                           user_id, get_audit_name_from_request(self), self.request.path)
            raise tornado.web.HTTPError(403, 'Access denied')

        return func(self, *args, **kwargs)

    return wrapper


def has_admin_rights(request_handler):
    user_id = _identify_user(request_handler)
    return request_handler.application.authorizer.is_admin(user_id)


class ProxiedRedirectHandler(tornado.web.RedirectHandler):
    def get(self, *args):
        redirect_relative(self._url.format(*args), self, *args)


class BaseRequestHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')

    def write_error(self, status_code, **kwargs):
        respond_error(self, status_code, self._reason)


class BaseStaticHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')


class GetServerConf(BaseRequestHandler):
    def get(self):
        self.write(external_model.server_conf_to_external(self.application.server_config))


class GetScripts(BaseRequestHandler):
    @check_authorization
    @inject_user
    def get(self, user):
        configs = self.application.config_service.list_configs(user)

        names = [conf.name for conf in configs]

        self.write(json.dumps(names))


class ScriptConfigSocket(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.config_model = None  # ConfigModel
        self.config_id = str(uuid.uuid4())

    @check_authorization
    @inject_user
    def open(self, user, config_name):
        try:
            self.config_model = self.application.config_service.create_config_model(config_name, user)
            active_config_models[self.config_id] = {'model': self.config_model, 'user_id': user.user_id}
        except ConfigNotAllowedException:
            self.close(code=403, reason='Access to the script is denied')
            return

        if not self.config_model:
            self.close(code=404, reason='Could not find a script by name')
            return

        self.ioloop = tornado.ioloop.IOLoop.current()

        initial_config = external_model.config_to_external(self.config_model, self.config_id)
        self.safe_write(wrap_to_server_event('initialConfig', initial_config))

        socket = self

        class ParameterListener:
            def on_add(self, parameter, index):
                socket.safe_write(wrap_to_server_event('parameterAdded', parameter_to_external(parameter)))
                socket._subscribe_on_parameter(parameter)

            def on_remove(self, parameter):
                socket.safe_write(wrap_to_server_event('parameterRemoved', parameter.name))

        self.config_model.parameters.subscribe(ParameterListener())
        for parameter in self.config_model.parameters:
            self._subscribe_on_parameter(parameter)

    def on_message(self, text):
        try:
            message = json.loads(text)

            type = message.get('event')
            data = message.get('data')

            if type == 'parameterValue':
                self._set_parameter_value(data.get('parameter'), data.get('value'))
                return

            LOGGER.warning('Unknown message received in ScriptConfigSocket: ' + text)
        except:
            LOGGER.exception('Failed to process message ' + text)

    def _set_parameter_value(self, parameter, value):
        self.config_model.set_param_value(parameter, value)

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

        self.safe_write(wrap_to_server_event('parameterChanged', external_param))

    def _subscribe_on_parameter(self, parameter):
        parameter.subscribe(lambda prop, old, new: self._send_parameter_changed(parameter))


class ScriptStop(BaseRequestHandler):
    @check_authorization
    def post(self, execution_id):
        validate_execution_id(execution_id, self)

        self.application.execution_service.stop_script(execution_id)


class ScriptStreamSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.executor = None

    @check_authorization
    def open(self, execution_id):
        auth = self.application.auth
        if not auth.is_authenticated(self):
            return None

        validate_execution_id(execution_id, self)

        execution_service = self.application.execution_service

        self.executor = execution_service.get_active_executor(execution_id)

        self.ioloop = tornado.ioloop.IOLoop.current()

        self.write_message(wrap_to_server_event('input', 'your input >>'))

        user_id = _identify_user(self)

        output_stream = execution_service.get_raw_output_stream(execution_id, user_id)
        pipe_output_to_http(output_stream, self.safe_write)

        downloads_folder = self.application.downloads_folder
        file_download_feature = self.application.file_download_feature
        web_socket = self

        def finished():
            try:
                downloadable_files = file_download_feature.get_downloadable_files(execution_id)

                for file in downloadable_files:
                    filename = os.path.basename(file)
                    relative_path = file_utils.relative_path(file, downloads_folder)

                    url_path = relative_path.replace(os.path.sep, '/')
                    url_path = 'result_files/' + url_path

                    web_socket.safe_write(wrap_to_server_event(
                        'file',
                        {'url': url_path, 'filename': filename}))
            except:
                LOGGER.exception('Could not prepare downloadable files')

            connection = web_socket.ws_connection
            if (connection is not None) and (hasattr(connection, 'ping_callback')):
                # we need to stop callback explicitly and as soon as possible, to avoid sending ping after close
                connection.ping_callback.stop()

            output_stream.wait_close(timeout=5)
            web_socket.ioloop.add_callback(web_socket.close, code=1000)

        execution_service.add_finish_listener(finished, execution_id)

    def on_message(self, text):
        self.executor.write_to_input(text)

    def on_close(self):
        audit_name = get_audit_name_from_request(self)
        LOGGER.info(audit_name + ' disconnected')

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.ioloop.add_callback(self.write_message, message)


@tornado.web.stream_request_body
class ScriptExecute(BaseRequestHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.form_reader = None

    @check_authorization
    def prepare(self):
        if self.request.method != 'POST':
            respond_error(self, 405, 'Method not allowed')
            return

        audit_name = get_audit_name_from_request(self)

        file_upload_feature = self.application.file_upload_feature
        upload_folder = file_upload_feature.prepare_new_folder(audit_name)

        self.request.connection.set_max_body_size(self.application.max_request_size_mb * BYTES_IN_MB)
        self.form_reader = StreamingFormReader(self.request.headers, upload_folder)

    def data_received(self, chunk):
        self.form_reader.read(chunk)

    @inject_user
    def post(self, user):
        script_name = None

        audit_name = user.get_audit_name()

        try:
            arguments = self.form_reader.values
            execution_info = external_model.to_execution_info(arguments)

            script_name = execution_info.script

            config_model = self.application.config_service.create_config_model(script_name, user)

            if not config_model:
                message = 'Script with name "' + str(script_name) + '" not found'
                LOGGER.error(message)
                respond_error(self, 400, message)
                return

            parameter_values = execution_info.param_values

            if self.form_reader.files:
                for key, value in self.form_reader.files.items():
                    parameter_values[key] = value.path

            try:
                config_model.set_all_param_values(parameter_values)
                normalized_values = dict(config_model.parameter_values)
            except InvalidValueException as e:
                message = 'Invalid parameter %s value: %s' % (e.param_name, str(e))
                LOGGER.error(message)
                respond_error(self, 400, message)
                return

            all_audit_names = user.audit_names
            LOGGER.info('Calling script %s. User %s', script_name, all_audit_names)

            execution_id = self.application.execution_service.start_script(
                config_model,
                normalized_values,
                user.user_id,
                all_audit_names)

            self.write(str(execution_id))

        except ConfigNotAllowedException:
            LOGGER.warning('Access to the script "' + script_name + '" is denied for ' + audit_name)
            respond_error(self, 403, 'Access to the script is denied')
            return

        except Exception as e:
            LOGGER.exception("Error while calling the script")

            if hasattr(e, "strerror") and e.strerror:
                error_output = e.strerror
            else:
                error_output = "Unknown error occurred, contact the administrator"

            result = " ---  ERRORS  --- \n"
            result += error_output

            if script_name:
                script = str(script_name)
            else:
                script = "Some script"

            audit_name = audit_name
            self.application.alerts_service.send_alert(
                script + ' NOT STARTED',
                "Couldn't start the script " + script + ' by ' + audit_name + '.\n\n'
                + result)

            respond_error(self, 500, result)


class GetActiveExecutionIds(BaseRequestHandler):
    @check_authorization
    def get(self):
        user_id = _identify_user(self)
        execution_service = self.application.execution_service

        active_executions = execution_service.get_active_executions(user_id)

        self.write(json.dumps(active_executions))


class GetExecutingScriptConfig(BaseRequestHandler):
    @check_authorization
    def get(self, execution_id):
        validate_execution_id(execution_id, self)

        config = self.application.execution_service.get_config(execution_id)

        values = dict(self.application.execution_service.get_user_parameter_values(execution_id))

        for parameter in config.parameters:
            parameter_name = parameter.name
            if (parameter_name in values) and (parameter.type == 'file_upload'):
                del values[parameter_name]

        self.write({
            'scriptName': config.name,
            'parameterValues': values
        })


class CleanupExecutingScript(BaseRequestHandler):
    @check_authorization
    def post(self, execution_id):
        validate_execution_id(execution_id, self)

        self.application.execution_service.cleanup_execution(execution_id)


class GetExecutionStatus(BaseRequestHandler):
    @check_authorization
    def get(self, execution_id):
        validate_execution_id(execution_id, self, only_active=False)

        running = self.application.execution_service.is_running(execution_id)
        self.write(external_model.running_flag_to_status(running))


def validate_execution_id(execution_id, request_handler, only_active=True):
    if is_empty(execution_id):
        raise tornado.web.HTTPError(400, reason='Execution id is missing')

    execution_service = request_handler.application.execution_service

    if only_active and (not execution_service.is_active(execution_id)):
        raise tornado.web.HTTPError(400, reason='No (active) executor found for id ' + execution_id)

    user_id = _identify_user(request_handler)
    if not execution_service.can_access(execution_id, user_id):
        LOGGER.warning('Prohibited access to not owned execution #%s (user=%s)',
                       execution_id, str(user_id))
        raise tornado.web.HTTPError(403, reason='Prohibited access to not owned execution')


class AuthorizedStaticFileHandler(BaseStaticHandler):
    admin_files = ['admin.html', 'css/admin.css', 'admin.js', 'admin-deps.css']

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        if not self.application.auth.is_enabled() and (absolute_path.endswith("/login.html")):
            raise tornado.web.HTTPError(404)

        relative_path = file_utils.relative_path(absolute_path, root)
        if self.is_admin_file(relative_path):
            if not has_admin_rights(self):
                user_id = _identify_user(self)
                LOGGER.warning('User %s (%s) tried to access admin static file %s',
                               user_id, get_audit_name_from_request(self), relative_path)
                raise tornado.web.HTTPError(403)

        return super(AuthorizedStaticFileHandler, self).validate_absolute_path(root, absolute_path)

    @classmethod
    def get_absolute_path(cls, root, path):
        path = path.lstrip('/')
        return super().get_absolute_path(root, path)

    def is_admin_file(self, relative_path):
        for admin_file in self.admin_files:
            if admin_file.endswith('*'):
                if relative_path.startswith(admin_file[:-1]):
                    return True
            elif relative_path == admin_file:
                return True

        return False


class ScriptParameterListFiles(BaseRequestHandler):

    @check_authorization
    @inject_user
    def get(self, user, script_name, parameter_name):
        id = self.get_query_argument('id')

        if not id:
            respond_error(self, 400, 'Model id is not specified')
            return

        if id not in active_config_models:
            respond_error(self, 400, 'Model with id=' + str(id) + ' does not exist')
            return

        active_model = active_config_models[id]
        config_user_id = active_model['user_id']

        if config_user_id != user.user_id:
            LOGGER.warning('User ' + str(user) + ' tried to access config '
                           + script_name + ' of user #' + config_user_id)
            respond_error(self, 400, 'Model with id=' + str(id) + ' does not exist')
            return

        config_model = active_model['model']

        if config_model.name != script_name:
            LOGGER.warning(
                'Config name differences for #' + str(id) + '. Expected ' + config_model.name + ', got ' + script_name)
            respond_error(self, 500, 'Failed to load script by name')
            return

        path = self.get_query_arguments('path')
        try:
            files = config_model.list_files_for_param(parameter_name, path)
            self.write(json.dumps(files))

        except ParameterNotFoundException as e:
            respond_error(self, 404, 'Parameter ' + e.param_name + ' does not exist')
            return
        except (InvalidValueException, WrongParameterUsageException) as e:
            respond_error(self, 400, str(e))
            return


class LoginHandler(BaseRequestHandler):
    def post(self):
        auth = self.application.auth
        return auth.authenticate(self)


class AuthInfoHandler(BaseRequestHandler):
    def get(self):
        auth = self.application.auth

        username = None
        if auth.is_enabled():
            username = auth.get_username(self)

        info = {
            'enabled': auth.is_enabled(),
            'username': username,
            'admin': has_admin_rights(self)
        }

        self.write(info)


class AuthConfigHandler(BaseRequestHandler):
    def get(self):
        auth = self.application.auth
        if not auth.is_enabled():
            raise tornado.web.HTTPError(404)

        self.write(auth.get_client_visible_config())


class LogoutHandler(BaseRequestHandler):
    @check_authorization
    def post(self):
        auth = self.application.auth

        auth.logout(self)


class DownloadResultFile(AuthorizedStaticFileHandler):
    def set_extra_headers(self, path):
        super().set_extra_headers(path)

        filename = os.path.basename(path)
        encoded_filename = urllib.parse.quote(filename, encoding='utf-8')
        self.set_header('Content-Disposition', 'attachment; filename*=UTF-8\'\'' + encoded_filename + '')

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        audit_name = get_audit_name_from_request(self)
        user_id = _identify_user(self)

        file_download_feature = self.application.file_download_feature

        file_path = file_utils.relative_path(absolute_path, os.path.abspath(root))
        if not file_download_feature.allowed_to_download(file_path, user_id):
            LOGGER.warning('Access attempt from ' + user_id + '(' + audit_name + ') to ' + absolute_path)
            raise tornado.web.HTTPError(403)

        return super(AuthorizedStaticFileHandler, self).validate_absolute_path(root, absolute_path)


# Use for testing only
class ReceiveAlertHandler(BaseRequestHandler):
    def post(self):
        body = tornado_utils.get_request_body(self)

        files = body.get('files', {})
        if files:
            del body['files']

        LOGGER.info('ReceiveAlertHandler. Received alert: ' + str(body))

        for key, value in files.items():
            filename = str(time.time()) + '_' + key

            LOGGER.info('ReceiveAlertHandler. Writing file ' + filename)

            file_path = os.path.join('logs', 'alerts', filename)
            file_utils.write_file(file_path, value)


class GetShortHistoryEntriesHandler(BaseRequestHandler):
    @check_authorization
    @requires_admin_rights
    def get(self):
        history_entries = self.application.execution_logging_service.get_history_entries()
        running_script_ids = []
        for entry in history_entries:
            if self.application.execution_service.is_running(entry.id):
                running_script_ids.append(entry.id)

        short_logs = to_short_execution_log(history_entries, running_script_ids)
        self.write(json.dumps(short_logs))


class GetLongHistoryEntryHandler(BaseRequestHandler):
    @check_authorization
    @requires_admin_rights
    def get(self, execution_id):
        if is_empty(execution_id):
            respond_error(self, 400, 'Execution id is not specified')
            return

        history_entry = self.application.execution_logging_service.find_history_entry(execution_id)
        if history_entry is None:
            respond_error(self, 400, 'No history found for id ' + execution_id)
            return

        log = self.application.execution_logging_service.find_log(execution_id)
        if is_empty(log):
            LOGGER.warning('No log found for execution ' + execution_id)

        running = self.application.execution_service.is_running(history_entry.id)
        long_log = to_long_execution_log(history_entry, log, running)
        self.write(json.dumps(long_log))


def wrap_to_server_event(event_type, data):
    return json.dumps({
        "event": event_type,
        "data": data
    })


def pipe_output_to_http(output_stream, write_callback):
    class OutputToHttpListener:
        def on_next(self, output):
            write_callback(wrap_to_server_event('output', output))

        def on_close(self):
            pass

    output_stream.subscribe(OutputToHttpListener())


def _identify_user(request_handler):
    user_id = request_handler.application.identification.identify(request_handler)

    if user_id is None:
        raise Exception('Could not identify user: ' + audit_utils.get_all_audit_names(request_handler))

    return user_id


def intercept_stop_when_running_scripts(io_loop, execution_service):
    def signal_handler(signum, frame):
        can_stop = True

        running_processes = execution_service.get_running_executions()
        if len(running_processes) > 0:
            try:
                user_input = input('Some scripts are still running. Do you want to stop server anyway? Y/N: \n')
                can_stop = (user_input.strip().lower()[0] == 'y')
            except EOFError:
                # EOF happens, when input is not available (e.g. when run under systemd)
                LOGGER.warning('Some scripts are still running, killing them forcefully')
                can_stop = True

            if can_stop:
                try:
                    LOGGER.info('Killing the running processes: ' + str(running_processes))
                    for id in running_processes:
                        execution_service.kill_script(id)
                except:
                    LOGGER.exception('Could not kill running scripts, trying to stop the server')

        if can_stop:
            LOGGER.info('Stopping server on interrupt')
            io_loop.add_callback(io_loop.stop)

    signal.signal(signal.SIGINT, signal_handler)


def init(server_config: ServerConfig,
         authenticator,
         authorizer,
         execution_service: ExecutionService,
         execution_logging_service: ExecutionLoggingService,
         config_service: ConfigService,
         alerts_service: AlertsService,
         file_upload_feature: FileUploadFeature,
         file_download_feature: FileDownloadFeature,
         secret):
    ssl_context = None
    if server_config.is_ssl():
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(server_config.get_ssl_cert_path(),
                                    server_config.get_ssl_key_path())

    auth = TornadoAuth(authenticator)
    if auth.is_enabled():
        identification = AuthBasedIdentification(auth)
    else:
        identification = IpBasedIdentification(server_config.trusted_ips)

    downloads_folder = file_download_feature.get_result_files_folder()

    handlers = [(r'/conf', GetServerConf),
                (r'/scripts', GetScripts),
                (r'/scripts/([^/]*)', ScriptConfigSocket),
                (r'/scripts/([^/]*)/([^/]*)/list-files', ScriptParameterListFiles),
                (r'/executions/start', ScriptExecute),
                (r'/executions/stop/(.*)', ScriptStop),
                (r'/executions/io/(.*)', ScriptStreamSocket),
                (r'/executions/active', GetActiveExecutionIds),
                (r'/executions/config/(.*)', GetExecutingScriptConfig),
                (r'/executions/cleanup/(.*)', CleanupExecutingScript),
                (r'/executions/status/(.*)', GetExecutionStatus),
                (r'/admin/execution_log/short', GetShortHistoryEntriesHandler),
                (r'/admin/execution_log/long/(.*)', GetLongHistoryEntryHandler),
                (r'/auth/info', AuthInfoHandler),
                (r'/result_files/(.*)',
                 DownloadResultFile,
                 {'path': downloads_folder}),
                (r"/", ProxiedRedirectHandler, {"url": "/index.html"})]

    if auth.is_enabled():
        handlers.append((r'/login', LoginHandler))
        handlers.append((r'/auth/config', AuthConfigHandler))
        handlers.append((r'/logout', LogoutHandler))

    handlers.append((r"/(.*)", AuthorizedStaticFileHandler, {"path": "web"}))

    settings = {
        "cookie_secret": secret,
        "login_url": "/login.html",
        'websocket_ping_interval': 30,
        'websocket_ping_timeout': 300
    }

    application = tornado.web.Application(handlers, **settings)

    application.auth = auth

    application.server_config = server_config
    application.authorizer = authorizer
    application.downloads_folder = downloads_folder
    application.file_download_feature = file_download_feature
    application.file_upload_feature = file_upload_feature
    application.execution_service = execution_service
    application.execution_logging_service = execution_logging_service
    application.config_service = config_service
    application.alerts_service = alerts_service
    application.identification = identification
    application.max_request_size_mb = server_config.max_request_size_mb

    io_loop = tornado.ioloop.IOLoop.current()

    http_server = httpserver.HTTPServer(application, ssl_options=ssl_context, max_buffer_size=10 * BYTES_IN_MB)
    http_server.listen(server_config.port, address=server_config.address)

    intercept_stop_when_running_scripts(io_loop, execution_service)

    http_protocol = 'https' if server_config.ssl else 'http'
    print('Server is running on: %s://%s:%s' % (http_protocol, server_config.address, server_config.port))
    io_loop.start()
