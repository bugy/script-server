#!/usr/bin/env python3
import json
import logging
import logging.config
import os
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
from alerts.alerts_service import AlertsService
from auth.tornado_auth import TornadoAuth
from execution.execution_service import ExecutionService
from execution.executor import ScriptExecutor
from execution.id_generator import IdGenerator
from execution.logging import ExecutionLoggingService
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from files.user_file_storage import UserFileStorage
from model import external_model
from model import model_helper
from model import script_configs
from model import server_conf
from model.external_model import to_short_execution_log, to_long_execution_log
from model.model_helper import is_empty
from utils import bash_utils as bash_utils, tornado_utils, audit_utils
from utils import file_utils as file_utils
from utils import os_utils as os_utils
from utils import tool_utils
from utils.audit_utils import get_all_audit_names, AUTH_USERNAME
from utils.audit_utils import get_audit_name
from utils.tornado_utils import respond_error, redirect_relative

TEMP_FOLDER = "temp"

CONFIG_FOLDER = "conf"
SERVER_CONF_PATH = os.path.join(CONFIG_FOLDER, "conf.json")
SCRIPT_CONFIGS_FOLDER = os.path.join(CONFIG_FOLDER, "runners")
LOGGER = logging.getLogger('script_server')


def list_config_names():
    def add_name(path, content):
        try:
            return script_configs.read_name(path, content)

        except:
            LOGGER.exception('Could not load script name: ' + path)

    result = visit_script_configs(add_name)

    return result


def load_config(name):
    def find_and_load(path, content):
        try:
            config_name = script_configs.read_name(path, content)
            if config_name == name:
                return script_configs.from_json(path, content, os_utils.is_pty_supported())
        except:
            LOGGER.exception('Could not load script config: ' + path)

    configs = visit_script_configs(find_and_load)
    if configs:
        return configs[0]

    return None


def visit_script_configs(visitor):
    configs_dir = SCRIPT_CONFIGS_FOLDER
    files = os.listdir(configs_dir)

    configs = [file for file in files if file.lower().endswith(".json")]

    result = []

    for config_path in configs:
        path = os.path.join(configs_dir, config_path)

        try:
            content = file_utils.read_file(path)

            visit_result = visitor(path, content)
            if visit_result is not None:
                result.append(visit_result)

        except:
            LOGGER.exception("Couldn't read the file: " + config_path)

    return result


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
            LOGGER.warning('User %s tried to access admin REST service %s', get_audit_name(self), self.request.path)
            raise tornado.web.HTTPError(403, 'Access denied')

        return func(self, *args, **kwargs)

    return wrapper


def has_admin_rights(request_handler):
    names = get_all_audit_names(request_handler)
    if AUTH_USERNAME in names:
        username = names[audit_utils.AUTH_USERNAME]
    else:
        username = names.get(audit_utils.IP)

    if not username:
        LOGGER.warning('has_admin_rights: could not resolve username for %s', get_audit_name(request_handler))
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
        config_names = list_config_names()

        self.write(json.dumps(config_names))


class GetScriptInfo(BaseRequestHandler):
    @check_authorization
    def get(self):
        try:
            name = self.get_query_argument("name")
        except tornado.web.MissingArgumentError:
            respond_error(self, 400, "Script name is not specified")
            return

        config = load_config(name)

        if not config:
            respond_error(self, 400, "Couldn't find a script by name")
            return

        self.write(external_model.config_to_json(config))


class ScriptStop(BaseRequestHandler):
    @check_authorization
    def post(self):
        request_body = self.request.body.decode("UTF-8")
        execution_id = json.loads(request_body).get('executionId')

        if execution_id:
            self.application.execution_service.stop_script(execution_id)
        else:
            respond_error(self, 400, "Invalid stop request")
            return


class ScriptStreamSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.executor = None

    def open(self, execution_id):
        auth = self.application.auth
        if not auth.is_authenticated(self):
            return None

        executor = self.application.execution_service.get_active_executor(execution_id)  # type: ScriptExecutor

        if not executor:
            raise Exception("Couldn't find corresponding process")

        self.executor = executor
        self.ioloop = tornado.ioloop.IOLoop.current()

        self.write_message(wrap_to_server_event("input", "your input >>"))

        self.write_message(wrap_script_output(" ---  OUTPUT  --- \n"))

        audit_name = get_audit_name(self)

        output_stream = executor.get_unsecure_output_stream()
        bash_formatting = executor.config.is_bash_formatting()
        pipe_output_to_http(output_stream, bash_formatting, self.safe_write)

        web_socket = self

        file_download_feature = self.application.file_download_feature

        class FinishListener(object):
            def finished(self):
                output_stream.wait_close()
                script_output = ''.join(output_stream.get_old_data())

                try:
                    downloadable_files = file_download_feature.prepare_downloadable_files(
                        executor.config,
                        script_output,
                        executor.parameter_values,
                        audit_name)

                    for file in downloadable_files:
                        filename = os.path.basename(file)
                        relative_path = file_utils.relative_path(file, TEMP_FOLDER)

                        web_socket.safe_write(wrap_to_server_event(
                            'file',
                            {'url': relative_path.replace(os.path.sep, '/'), 'filename': filename}))
                except:
                    LOGGER.exception("Couldn't prepare downloadable files")

                web_socket.ioloop.add_callback(web_socket.close)

        executor.add_finish_listener(FinishListener())

    def on_message(self, text):
        self.executor.write_to_input(text)

    def on_close(self):
        if self.executor.config.kill_on_disconnect:
            self.executor.kill()

        audit_name = get_audit_name(self)
        LOGGER.info(audit_name + ' disconnected')

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.ioloop.add_callback(self.write_message, message)


class ScriptExecute(BaseRequestHandler):
    @check_authorization
    def post(self):
        script_name = None

        audit_name = get_audit_name(self)

        try:
            arguments = tornado_utils.get_form_arguments(self)
            execution_info = external_model.to_execution_info(arguments)

            script_name = execution_info.script

            config = load_config(script_name)

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

            LOGGER.info('Calling script ' + script_name + '. User ' + str(get_all_audit_names(self)))

            execution_id = self.application.execution_service.start_script(
                config,
                execution_info.param_values,
                audit_name)

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


class AuthorizedStaticFileHandler(BaseStaticHandler):
    admin_files = ['css/admin.css', 'js/admin/*', 'admin.html']

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        if not self.application.auth.is_enabled() and (absolute_path.endswith("/login.html")):
            raise tornado.web.HTTPError(404)

        relative_path = file_utils.relative_path(absolute_path, root)
        if self.is_admin_file(relative_path):
            if not has_admin_rights(self):
                LOGGER.warning('User %s tried to access admin static file %s', get_audit_name(self), relative_path)
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
        audit_name = get_audit_name(self)

        file_download_feature = self.application.file_download_feature

        file_path = file_utils.relative_path(absolute_path, os.path.abspath(root))
        if not file_download_feature.allowed_to_download(file_path, audit_name):
            LOGGER.warning('Access attempt from ' + audit_name + ' to ' + absolute_path)
            raise tornado.web.HTTPError(404)

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


def wrap_script_output(text, text_color=None, background_color=None, text_styles=None):
    output_object = {'text': text}

    if text_color:
        output_object['text_color'] = text_color

    if background_color:
        output_object['background_color'] = background_color

    if text_styles:
        output_object['text_styles'] = text_styles

    return wrap_to_server_event("output", output_object)


def wrap_to_server_event(event_type, data):
    return json.dumps({
        "event": event_type,
        "data": data
    })


def pipe_output_to_http(output_stream, bash_formatting, write_callback):
    reader = None
    if bash_formatting:
        reader = bash_utils.BashReader()

    class OutputToHttpListener:
        def on_next(self, output):
            if reader:
                read_iterator = reader.read(output)
                for text in read_iterator:
                    write_callback(wrap_script_output(
                        text.text,
                        text.text_color,
                        text.background_color,
                        text.styles
                    ))

            else:
                write_callback(wrap_script_output(output))

        def on_close(self):
            pass

    output_stream.subscribe(OutputToHttpListener())


def get_tornado_secret():
    secret_file = os.path.join("temp", "secret.dat")
    if os.path.exists(secret_file):
        secret = file_utils.read_file(secret_file, byte_content=True)
        if secret:
            return secret

    secret = os.urandom(256)
    file_utils.write_file(secret_file, secret, byte_content=True)
    return secret


def main():
    tool_utils.validate_web_imports_exist(os.getcwd())

    logging_conf_file = os.path.join(CONFIG_FOLDER, 'logging.json')
    with open(logging_conf_file, "rt") as f:
        log_config = json.load(f)
        file_utils.prepare_folder(os.path.join('logs'))

        logging.config.dictConfig(log_config)

    file_utils.prepare_folder(CONFIG_FOLDER)
    file_utils.prepare_folder(SCRIPT_CONFIGS_FOLDER)

    server_config = server_conf.from_json(SERVER_CONF_PATH)
    ssl_context = None
    if server_config.is_ssl():
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(server_config.get_ssl_cert_path(),
                                    server_config.get_ssl_key_path())

    file_utils.prepare_folder(TEMP_FOLDER)

    settings = {
        "cookie_secret": get_tornado_secret(),
        "login_url": "/login.html"
    }

    auth = TornadoAuth(server_config.authenticator, server_config.authorizer)

    user_file_storage = UserFileStorage(get_tornado_secret())
    file_download_feature = FileDownloadFeature(user_file_storage, TEMP_FOLDER)
    result_files_folder = file_download_feature.get_result_files_folder()

    handlers = [(r"/conf/title", GetServerTitle),
                (r"/scripts/list", GetScripts),
                (r"/scripts/info", GetScriptInfo),
                (r"/scripts/execute", ScriptExecute),
                (r"/scripts/execute/stop", ScriptStop),
                (r"/scripts/execute/io/(.*)", ScriptStreamSocket),
                (r'/admin/execution_log/short', GetShortHistoryEntriesHandler),
                (r'/admin/execution_log/long/(.*)', GetLongHistoryEntryHandler),
                (r'/' + os.path.basename(result_files_folder) + '/(.*)',
                 DownloadResultFile,
                 {'path': result_files_folder}),
                (r"/", ProxiedRedirectHandler, {"url": "/index.html"})]

    if auth.is_enabled():
        handlers.append((r'/login', LoginHandler))
        handlers.append((r'/auth/config', AuthConfigHandler))
        handlers.append((r'/logout', LogoutHandler))

    handlers.append((r"/username", GetUsernameHandler))

    handlers.append((r"/(.*)", AuthorizedStaticFileHandler, {"path": "web"}))

    application = tornado.web.Application(handlers, **settings)

    application.auth = auth

    application.server_title = server_config.title
    application.authorizer = server_config.authorizer

    application.file_download_feature = file_download_feature
    application.file_upload_feature = FileUploadFeature(user_file_storage, TEMP_FOLDER)

    alerts_service = AlertsService(server_config.get_alerts_config())
    application.alerts_service = alerts_service

    execution_logs_path = os.path.join('logs', 'processes')
    execution_logging_service = ExecutionLoggingService(execution_logs_path)
    application.execution_logging_service = execution_logging_service

    existing_ids = [entry.id for entry in execution_logging_service.get_history_entries()]
    id_generator = IdGenerator(existing_ids)

    execution_service = ExecutionService(execution_logging_service, alerts_service, id_generator)
    application.execution_service = execution_service

    http_server = httpserver.HTTPServer(application, ssl_options=ssl_context)
    http_server.listen(server_config.port, address=server_config.address)

    http_protocol = 'https' if server_config.ssl else 'http'
    print('Server is running on: %s://%s:%s' % (http_protocol, server_config.address, server_config.port))

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
