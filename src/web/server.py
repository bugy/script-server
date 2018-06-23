#!/usr/bin/env python3
import json
import logging.config
import os
import signal
import ssl
import time
from urllib.parse import urlencode
from urllib.parse import urlparse

import tornado.concurrent
import tornado.escape
import tornado.httpserver as httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from auth.tornado_auth import TornadoAuth
from config.config_service import ConfigService
from execution.execution_service import ExecutionService
from execution.logging import ExecutionLoggingService
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from model import external_model
from model import model_helper
from model.external_model import to_short_execution_log, to_long_execution_log
from model.model_helper import is_empty
from model.server_conf import ServerConfig
from utils import file_utils as file_utils
from utils import tornado_utils, audit_utils
from utils.audit_utils import get_all_audit_names, get_safe_username
from utils.audit_utils import get_audit_name_from_request
from utils.terminal_formatter import TerminalOutputTransformer, TerminalOutputChunk
from utils.tornado_utils import respond_error, redirect_relative

LOGGER = logging.getLogger('web_server')


def is_allowed_during_login(request_path, login_url, request_handler):
    if request_handler.request.method != 'GET':
        return False

    if request_path == '/favicon.ico':
        return True

    if request_path == login_url:
        return True

    login_resources = ['/js/login.js',
                       '/js/common.js',
                       '/js/libs/jquery.min.js',
                       '/js/libs/materialize.min.js',
                       '/css/libs/materialize.min.css',
                       '/css/index.css',
                       '/css/fonts/roboto/Roboto-Regular.woff2',
                       '/css/fonts/roboto/Roboto-Regular.woff',
                       '/css/fonts/roboto/Roboto-Regular.ttf',
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

    allowed_referrers = [login_url, '/css/libs/materialize.min.css', '/css/index.css']
    for allowed_referrer in allowed_referrers:
        if referer.endswith(allowed_referrer):
            return True


# In case of REST requests we don't redirect explicitly, but reply with Unauthorized code.
# Client application should provide redirection in the way it likes
def check_authorization(func):
    def wrapper(self, *args, **kwargs):
        auth = self.application.auth
        request_path = self.request.path
        login_url = self.get_login_url()

        if (auth.is_authenticated(self) and (auth.is_authorized(self))) \
                or is_allowed_during_login(request_path, login_url, self):
            return func(self, *args, **kwargs)

        if not isinstance(self, tornado.web.StaticFileHandler):
            if not auth.is_authenticated(self):
                raise tornado.web.HTTPError(401, 'Not authenticated')
            else:
                raise tornado.web.HTTPError(403, 'Access denied')

        login_url += "?" + urlencode(dict(next=request_path))

        redirect_relative(login_url, self)

        return

    return wrapper


def requires_admin_rights(func):
    def wrapper(self, *args, **kwargs):
        if not has_admin_rights(self):
            LOGGER.warning('User %s tried to access admin REST service %s',
                           get_audit_name_from_request(self), self.request.path)
            raise tornado.web.HTTPError(403, 'Access denied')

        return func(self, *args, **kwargs)

    return wrapper


def has_admin_rights(request_handler):
    names = get_all_audit_names(request_handler)

    username = audit_utils.get_safe_username(names)

    if not username:
        LOGGER.warning('has_admin_rights: could not resolve username for %s',
                       get_audit_name_from_request(request_handler))
        return False

    return request_handler.application.authorizer.is_admin(username)


class ProxiedRedirectHandler(tornado.web.RedirectHandler):
    def get(self, *args):
        redirect_relative(self._url.format(*args), self, *args)


class BaseRequestHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')


class BaseStaticHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')


class GetServerTitle(BaseRequestHandler):
    def get(self):
        if self.application.server_title:
            self.write(self.application.server_title)


class GetScripts(BaseRequestHandler):
    @check_authorization
    def get(self):
        config_names = self.application.config_service.list_config_names()

        self.write(json.dumps(config_names))


class GetScriptInfo(BaseRequestHandler):
    @check_authorization
    def get(self):
        try:
            name = self.get_query_argument("name")
        except tornado.web.MissingArgumentError:
            respond_error(self, 400, "Script name is not specified")
            return

        config = self.application.config_service.load_config(name)

        if not config:
            respond_error(self, 400, "Couldn't find a script by name")
            return

        self.write(external_model.config_to_json(config))


class ScriptStop(BaseRequestHandler):
    @check_authorization
    def post(self, execution_id):
        validate_execution_id(execution_id, self)

        self.application.execution_service.stop_script(execution_id)


class ScriptStreamSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.executor = None

    def open(self, execution_id):
        auth = self.application.auth
        if not auth.is_authenticated(self):
            return None

        validate_execution_id(execution_id, self)

        execution_service = self.application.execution_service

        config = execution_service.get_config(execution_id)
        self.executor = execution_service.get_active_executor(execution_id)

        self.ioloop = tornado.ioloop.IOLoop.current()

        self.write_message(wrap_to_server_event('input', 'your input >>'))

        audit_names = audit_utils.get_all_audit_names(self)
        output_stream = execution_service.get_raw_output_stream(execution_id, audit_names)
        bash_formatting = config.is_bash_formatting()
        pipe_output_to_http(output_stream, bash_formatting, self.safe_write)

        def finished(web_socket, downloads_folder, file_download_feature):
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
            if connection is not None:
                # we need to stop callback explicitly and as soon as possible, to avoid sending ping after close
                connection.ping_callback.stop()

            web_socket.ioloop.add_callback(web_socket.close, code=1000)

        output_stream.subscribe_on_close(finished,
                                         self,
                                         self.application.downloads_folder,
                                         self.application.file_download_feature)

    def on_message(self, text):
        self.executor.write_to_input(text)

    def on_close(self):
        audit_name = get_audit_name_from_request(self)
        LOGGER.info(audit_name + ' disconnected')

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.ioloop.add_callback(self.write_message, message)


class ScriptExecute(BaseRequestHandler):
    @check_authorization
    def post(self):
        script_name = None

        audit_name = get_audit_name_from_request(self)

        try:
            arguments = tornado_utils.get_form_arguments(self)
            execution_info = external_model.to_execution_info(arguments)

            script_name = execution_info.script

            config = self.application.config_service.load_config(script_name)

            if not config:
                message = 'Script with name "' + str(script_name) + '" not found'
                LOGGER.error(message)
                respond_error(self, 400, message)
                return

            file_upload_feature = self.application.file_upload_feature
            if self.request.files:
                for key, value in self.request.files.items():
                    file_info = value[0]
                    file_path = file_upload_feature.save_file(file_info.filename, file_info.body, audit_name)
                    execution_info.param_values[key] = file_path

            valid_parameters = model_helper.validate_parameters(execution_info.param_values, config)
            if not valid_parameters:
                message = 'Received invalid parameters'
                LOGGER.error(message)
                respond_error(self, 400, message)
                return

            all_audit_names = get_all_audit_names(self)
            LOGGER.info('Calling script ' + script_name + '. User ' + str(all_audit_names))

            execution_id = self.application.execution_service.start_script(
                config,
                execution_info.param_values,
                all_audit_names)

            self.write(str(execution_id))

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
        all_audit_names = audit_utils.get_all_audit_names(self)
        execution_service = self.application.execution_service

        active_executions = execution_service.get_active_executions(all_audit_names)

        self.write(json.dumps(active_executions))


class GetExecutingScriptConfig(BaseRequestHandler):
    @check_authorization
    def get(self, execution_id):
        validate_execution_id(execution_id, self)

        config = self.application.execution_service.get_config(execution_id)

        self.write(external_model.config_to_json(config))


class GetExecutingScriptValues(BaseRequestHandler):
    @check_authorization
    def get(self, execution_id):
        validate_execution_id(execution_id, self)

        values = self.application.execution_service.get_parameter_values(execution_id)

        self.write(external_model.to_external_parameter_values(values))


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

    all_audit_names = audit_utils.get_all_audit_names(request_handler)
    if not execution_service.can_access(execution_id, all_audit_names):
        LOGGER.warning('Prohibited access to not owned execution #%s (user=%s)',
                       execution_id, str(all_audit_names))
        raise tornado.web.HTTPError(403, reason='Prohibited access to not owned execution')


class AuthorizedStaticFileHandler(BaseStaticHandler):
    admin_files = ['css/admin.css', 'js/admin/*', 'admin.html']

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        if not self.application.auth.is_enabled() and (absolute_path.endswith("/login.html")):
            raise tornado.web.HTTPError(404)

        relative_path = file_utils.relative_path(absolute_path, root)
        if self.is_admin_file(relative_path):
            if not has_admin_rights(self):
                LOGGER.warning('User %s tried to access admin static file %s',
                               get_audit_name_from_request(self), relative_path)
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


class LoginHandler(BaseRequestHandler):
    def post(self):
        auth = self.application.auth
        return auth.authenticate(self)


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


class GetUsernameHandler(BaseRequestHandler):
    @check_authorization
    def get(self):
        auth = self.application.auth
        if not auth.is_enabled():
            raise tornado.web.HTTPError(404)

        username = auth.get_username(self)
        self.write(username)


class DownloadResultFile(AuthorizedStaticFileHandler):
    def set_extra_headers(self, path):
        super().set_extra_headers(path)

        filename = os.path.basename(path)
        self.set_header('Content-Disposition', 'attachment; filename=' + filename + '')

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        audit_name = get_audit_name_from_request(self)
        username = get_safe_username(get_all_audit_names(self))

        file_download_feature = self.application.file_download_feature

        file_path = file_utils.relative_path(absolute_path, os.path.abspath(root))
        if not file_download_feature.allowed_to_download(file_path, username):
            LOGGER.warning('Access attempt from ' + username + '(' + audit_name + ') to ' + absolute_path)
            raise tornado.web.HTTPError(403)

        return super(AuthorizedStaticFileHandler, self).validate_absolute_path(root, absolute_path)


# Use for testing only
class ReceiveAlertHandler(BaseRequestHandler):
    def post(self):
        message = self.get_body_argument('message')
        LOGGER.info('ReceiveAlertHandler. Received alert: ' + message)

        log_files = self.request.files['log']
        if log_files:
            file = log_files[0]
            filename = str(time.time()) + '_' + file.filename

            LOGGER.info('ReceiveAlertHandler. Writing file ' + filename)

            file_path = os.path.join('logs', 'alerts', filename)
            file_utils.write_file(file_path, file.body.decode('utf-8'))


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


def wrap_script_output(text, text_color=None, background_color=None, text_styles=None, custom_position=None):
    output_object = {'text': text}

    if text_color:
        output_object['text_color'] = text_color

    if background_color:
        output_object['background_color'] = background_color

    if text_styles:
        output_object['text_styles'] = text_styles

    if custom_position:
        output_object['replace'] = True
        output_object['custom_position'] = {'x': custom_position.x, 'y': custom_position.y}

    return wrap_to_server_event('output', output_object)


def wrap_to_server_event(event_type, data):
    return json.dumps({
        "event": event_type,
        "data": data
    })


def pipe_output_to_http(output_stream, bash_formatting, write_callback):
    if bash_formatting:

        terminal_output_stream = TerminalOutputTransformer(output_stream)

        class OutputToHttpListener:
            def on_next(self, terminal_output: TerminalOutputChunk):
                formatted_text = terminal_output.formatted_text
                custom_position = terminal_output.custom_position

                write_callback(wrap_script_output(
                    formatted_text.text,
                    text_color=formatted_text.text_color,
                    background_color=formatted_text.background_color,
                    text_styles=formatted_text.styles,
                    custom_position=custom_position))

            def on_close(self):
                terminal_output_stream.dispose()
                pass

        terminal_output_stream.subscribe(OutputToHttpListener())

    else:
        class OutputToHttpListener:
            def on_next(self, output):
                write_callback(wrap_script_output(output))

            def on_close(self):
                pass

        output_stream.subscribe(OutputToHttpListener())


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
         execution_service: ExecutionService,
         execution_logging_service: ExecutionLoggingService,
         config_service: ConfigService,
         file_upload_feature: FileUploadFeature,
         file_download_feature: FileDownloadFeature,
         secret):

    ssl_context = None
    if server_config.is_ssl():
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(server_config.get_ssl_cert_path(),
                                    server_config.get_ssl_key_path())

    auth = TornadoAuth(server_config.authenticator, server_config.authorizer)

    downloads_folder = file_download_feature.get_result_files_folder()

    handlers = [(r"/conf/title", GetServerTitle),
                (r"/scripts/list", GetScripts),
                (r"/scripts/info", GetScriptInfo),
                (r"/scripts/execution", ScriptExecute),
                (r"/scripts/execution/stop/(.*)", ScriptStop),
                (r"/scripts/execution/io/(.*)", ScriptStreamSocket),
                (r"/scripts/execution/active", GetActiveExecutionIds),
                (r"/scripts/execution/config/(.*)", GetExecutingScriptConfig),
                (r"/scripts/execution/values/(.*)", GetExecutingScriptValues),
                (r"/scripts/execution/cleanup/(.*)", CleanupExecutingScript),
                (r"/scripts/execution/status/(.*)", GetExecutionStatus),
                (r'/admin/execution_log/short', GetShortHistoryEntriesHandler),
                (r'/admin/execution_log/long/(.*)', GetLongHistoryEntryHandler),
                (r'/result_files/(.*)',
                 DownloadResultFile,
                 {'path': downloads_folder}),
                (r"/", ProxiedRedirectHandler, {"url": "/index.html"})]

    if auth.is_enabled():
        handlers.append((r'/login', LoginHandler))
        handlers.append((r'/auth/config', AuthConfigHandler))
        handlers.append((r'/logout', LogoutHandler))

    handlers.append((r"/username", GetUsernameHandler))

    handlers.append((r"/(.*)", AuthorizedStaticFileHandler, {"path": "web"}))

    settings = {
        "cookie_secret": secret,
        "login_url": "/login.html",
        'websocket_ping_interval': 30,
        'websocket_ping_timeout': 300
    }

    application = tornado.web.Application(handlers, **settings)

    application.auth = auth

    application.server_title = server_config.title
    application.authorizer = server_config.authorizer
    application.downloads_folder = downloads_folder
    application.file_download_feature = file_download_feature
    application.file_upload_feature = file_upload_feature
    application.execution_service = execution_service
    application.execution_logging_service = execution_logging_service
    application.config_service = config_service

    io_loop = tornado.ioloop.IOLoop.current()

    http_server = httpserver.HTTPServer(application, ssl_options=ssl_context)
    http_server.listen(server_config.port, address=server_config.address)

    intercept_stop_when_running_scripts(io_loop, execution_service)

    http_protocol = 'https' if server_config.ssl else 'http'
    print('Server is running on: %s://%s:%s' % (http_protocol, server_config.address, server_config.port))
    io_loop.start()
