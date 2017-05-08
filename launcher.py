import json
import logging
import logging.config
import os
import shlex
import socket
import ssl
import sys
import threading
from datetime import datetime
from urllib.parse import urlencode
from urllib.parse import urlparse

import tornado.escape
import tornado.httpserver as httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import auth.auth_base as auth_base
import execution
import execution_popen
import external_model
import file_download_feature
import model_helper
import script_configs
import server_conf
import utils.bash_utils as bash_utils
import utils.file_utils as file_utils

TEMP_FOLDER = "temp"

pty_supported = (sys.platform == "linux" or sys.platform == "linux2")
if pty_supported:
    import execution_pty

CONFIG_FOLDER = "conf"
SERVER_CONF_PATH = os.path.join(CONFIG_FOLDER, "conf.json")
SCRIPT_CONFIGS_FOLDER = os.path.join(CONFIG_FOLDER, "runners")

running_scripts = {}


def list_config_names():
    def add_name(path, content):
        try:
            return script_configs.read_name(path, content)

        except:
            logger = logging.getLogger("scriptServer")
            logger.exception("Could not load script name: " + path)

    result = visit_script_configs(add_name)

    return result


def load_config(name):
    def find_and_load(path, content):
        try:
            config_name = script_configs.read_name(path, content)
            if config_name == name:
                return script_configs.from_json(path, content, pty_supported)
        except:
            logger = logging.getLogger("scriptServer")
            logger.exception("Could not load script config: " + path)

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
            logger = logging.getLogger('scriptServer')
            logger.exception("Couldn't read the file: " + config_path)

    return result


class TornadoAuth():
    authorizer = None

    def __init__(self, authorizer):
        self.authorizer = authorizer

    def is_enabled(self):
        return bool(self.authorizer)

    def is_authenticated(self, request_handler):
        if not self.is_enabled():
            return True

        username = request_handler.get_secure_cookie("username")

        return bool(username)

    def get_username(self, request_handler):
        if not self.is_enabled():
            return None

        username = request_handler.get_secure_cookie("username")
        if not username:
            return None

        return username.decode("utf-8")

    def authenticate(self, username, password, request_handler):
        logger = logging.getLogger("scriptServer")

        logger.info("Trying to authenticate user " + username)

        try:
            self.authorizer.authenticate(username, password)
            logger.info("Authenticated user " + username)

        except auth_base.AuthRejectedError as e:
            logger.info("Authentication rejected for user " + username + ": " + e.get_message())
            respond_error(request_handler, 401, e.get_message())
            return

        except auth_base.AuthFailureError:
            logger.exception("Authentication failed for user " + username)
            respond_error(request_handler, 500, "Something went wrong. Please contact the administrator or try later")
            return

        request_handler.set_secure_cookie("username", username)

        path = tornado.escape.url_unescape(request_handler.get_argument("next", "/"))
        request_handler.redirect(path)

    def logout(self, request_handler):
        if not self.is_enabled():
            return

        username = self.get_username(request_handler)
        if not username:
            return

        logger = logging.getLogger("scriptServer")
        logger.info("Logging out " + username)

        request_handler.clear_cookie("username")


def is_allowed_during_login(request_path, login_url, request_handler):
    if request_handler.request.method == "POST":
        if request_path == "/login":
            return True

    elif request_handler.request.method == "GET":
        if request_path == "/favicon.ico":
            return True

        if request_path == login_url:
            return True

        referer = request_handler.request.headers.get("Referer")
        if referer:
            referer = urlparse(referer).path

        login_resources = ["/js/login.js",
                           "/js/common.js",
                           "/js/libs/jquery.min.js",
                           "/js/libs/materialize.min.js",
                           "/css/libs/materialize.min.css",
                           "/css/index.css",
                           "/css/fonts/roboto/Roboto-Regular.woff2",
                           "/css/fonts/roboto/Roboto-Regular.woff",
                           "/css/fonts/roboto/Roboto-Regular.ttf",
                           "/images/titleBackground.jpg"]

        if ((referer == login_url) or (referer == "/css/libs/materialize.min.css") or (referer == "/css/index.css")) \
                and (request_path in login_resources):
            return True

    return False


# This decorator is used for REST requests, in which we don't redirect explicitly, but reply with Unauthorized code.
# Client application should provide redirection in the way it likes
def check_authorization(func):
    def wrapper(self, *args, **kwargs):
        auth = self.application.auth
        request_path = self.request.path
        login_url = self.get_login_url()

        if auth.is_authenticated(self) or is_allowed_during_login(request_path, login_url, self):
            return func(self, *args, **kwargs)

        if not isinstance(self, tornado.web.StaticFileHandler):
            raise tornado.web.HTTPError(401, "Unauthorized")

        login_url += "?" + urlencode(dict(next=request_path))

        self.redirect(login_url)
        return

    return wrapper


class GetScripts(tornado.web.RequestHandler):
    @check_authorization
    def get(self):
        config_names = list_config_names()

        self.write(json.dumps(config_names))


class GetScriptInfo(tornado.web.RequestHandler):
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


def build_parameter_string(param_values, config):
    result = []

    for parameter in config.get_parameters():
        name = parameter.get_name()

        if parameter.is_constant():
            param_values[parameter.name] = model_helper.get_default(parameter)

        if name in param_values:
            value = param_values[name]

            if parameter.is_no_value():
                # do not replace == True, since REST service can start accepting boolean as string
                if (value == True) or (value == "true"):
                    result.append(parameter.get_param())
            else:
                if value:
                    if parameter.get_param():
                        result.append(parameter.get_param())

                    result.append(value)

    return result


def stop_script(process_id):
    if process_id in running_scripts:
        running_scripts[process_id].stop()


class ScriptStop(tornado.web.RequestHandler):
    @check_authorization
    def post(self):
        request_body = self.request.body.decode("UTF-8")
        process_id = json.loads(request_body).get("processId")

        if (process_id):
            stop_script(int(process_id))
        else:
            respond_error(self, 400, "Invalid stop request")
            return


class ScriptStreamsSocket(tornado.websocket.WebSocketHandler):
    process_wrapper = None
    reading_thread = None

    def open(self, process_id):
        auth = self.application.auth
        if not auth.is_authenticated(self):
            return None

        logger = logging.getLogger("scriptServer")

        self.process_wrapper = running_scripts.get(int(process_id))

        if not self.process_wrapper:
            raise Exception("Couldn't find corresponding process")

        self.write_message(wrap_to_server_event("input", "your input >>"))

        self.write_message(wrap_script_output(" ---  OUTPUT  --- \n"))

        audit_name = get_audit_name(self, logger)

        command_identifier = self.process_wrapper.get_command_identifier()
        launch_identifier = self.create_log_identifier(audit_name, command_identifier)

        reading_thread = threading.Thread(target=pipe_process_to_http, args=(
            self.process_wrapper,
            launch_identifier,
            self.safe_write
        ))
        reading_thread.start()

        web_socket = self
        process_wrapper = self.process_wrapper

        class FinishListener(object):
            def finished(self):
                reading_thread.join()

                try:
                    downloadable_files = file_download_feature.prepare_downloadable_files(
                        process_wrapper.get_config(),
                        process_wrapper.get_full_output(),
                        audit_name,
                        get_tornado_secret(),
                        TEMP_FOLDER)

                    for file in downloadable_files:
                        filename = os.path.basename(file)
                        relative_path = file_utils.relative_path(file, TEMP_FOLDER)

                        web_socket.safe_write(wrap_to_server_event(
                            'file',
                            {'url': relative_path.replace(os.path.sep, '/'), 'filename': filename}))
                except:
                    logger.exception("Couldn't prepare downloadable files")

                web_socket.close()

        self.process_wrapper.add_finish_listener(FinishListener())

    @staticmethod
    def create_log_identifier(audit_name, command_identifier):
        if sys.platform.startswith('win'):
            audit_name = audit_name.replace(":", "-")

        date_string = datetime.today().strftime("%y%m%d_%H%M%S")
        command_identifier = command_identifier.replace(" ", "_")
        log_identifier = command_identifier + "_" + audit_name + "_" + date_string
        return log_identifier

    def on_message(self, text):
        self.process_wrapper.write_to_input(text)

    def on_close(self):
        if not self.process_wrapper.is_finished():
            self.process_wrapper.kill()

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.write_message(message)


def get_audit_name(request_handler, logger):
    auth = request_handler.application.auth

    username = auth.get_username(request_handler)
    if username:
        audit_name = username
    else:
        remote_ip = request_handler.request.remote_ip
        try:
            (hostname, aliases, ip_addresses) = socket.gethostbyaddr(remote_ip)
            audit_name = hostname
        except:
            audit_name = None
            logger.warn("Couldn't get hostname for " + remote_ip)

        if not audit_name:
            audit_name = remote_ip

    return audit_name


class ScriptExecute(tornado.web.RequestHandler):
    process_wrapper = None

    @check_authorization
    def post(self):
        script_name = None

        try:
            request_data = self.request.body

            execution_info = external_model.to_execution_info(request_data.decode("UTF-8"))

            script_name = execution_info.get_script()

            config = load_config(script_name)

            if not config:
                respond_error(self, 400, "Script with name '" + str(script_name) + "' not found")

            working_directory = config.get_working_directory()
            if working_directory is not None:
                working_directory = file_utils.normalize_path(working_directory)

            (script_path, body_args) = self.parse_script_body(config, working_directory)

            script_args = build_parameter_string(execution_info.get_param_values(), config)

            command = []
            command.append(script_path)
            command.extend(body_args)
            command.extend(script_args)

            script_logger = logging.getLogger("scriptServer")
            audit_name = get_audit_name(self, script_logger)

            script_logger.info("Calling script (by " + audit_name + "): " + " ".join(command))

            run_pty = config.is_requires_terminal()
            if run_pty and not pty_supported:
                script_logger.warn(
                    "Requested PTY mode, but it's not supported for this OS (" + sys.platform + "). Falling back to POpen")
                run_pty = False

            if run_pty:
                self.process_wrapper = execution_pty.PtyProcessWrapper(command,
                                                                       config.get_name(),
                                                                       working_directory,
                                                                       config)
            else:
                self.process_wrapper = execution_popen.POpenProcessWrapper(command,
                                                                           config.get_name(),
                                                                           working_directory,
                                                                           config)

            process_id = self.process_wrapper.get_process_id()

            running_scripts[process_id] = self.process_wrapper

            self.write(str(process_id))

            alerts_config = self.application.alerts_config
            if alerts_config:
                self.subscribe_fail_alerter(script_name, script_logger, alerts_config)


        except Exception as e:
            script_logger = logging.getLogger("scriptServer")
            script_logger.exception("Error while calling the script")

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

            audit_name = get_audit_name(self, script_logger)
            send_alerts(self.application.alerts_config, script + ' NOT STARTED',
                        "Couldn't start the script " + script + ' by ' + audit_name + '.\n\n' +
                        result)

            respond_error(self, 500, result)

    def subscribe_fail_alerter(self, script_name, script_logger, alerts_config):
        request_handler_self = self

        class Alerter(object):
            def finished(self):
                return_code = request_handler_self.process_wrapper.get_return_code()

                if return_code != 0:
                    script = str(script_name)

                    audit_name = get_audit_name(request_handler_self, script_logger)

                    title = script + ' FAILED'
                    body = 'The script "' + script + '", started by ' + audit_name + \
                           ' exited with return code ' + str(return_code) + '.' + \
                           ' Usually this means an error, occurred during the execution.' + \
                           ' Please check the corresponding logs'

                    send_alerts(alerts_config, title, body)

        self.process_wrapper.add_finish_listener(Alerter())

    def parse_script_body(self, config, working_directory):
        script_body = config.get_script_body()
        if (' ' in script_body) and (not sys.platform.startswith('win')):
            args = shlex.split(script_body)
            script_path = file_utils.normalize_path(args[0], working_directory)
            body_args = args[1:]
            for i, body_arg in enumerate(body_args):
                expanded = os.path.expanduser(body_arg)
                if expanded != body_arg:
                    body_args[i] = expanded
        else:
            script_path = file_utils.normalize_path(script_body, working_directory)
            body_args = []

        return script_path, body_args


def send_alerts(alerts_config, title, body):
    if (not alerts_config) or (not alerts_config.get_destinations()):
        return

    def _send():
        for destination in alerts_config.get_destinations():
            try:
                destination.send(title, body)
            except:
                script_logger = logging.getLogger("scriptServer")
                script_logger.exception("Couldn't send alert to " + str(destination))

    thread = threading.Thread(target=_send)
    thread.start()


class AuthorizedStaticFileHandler(tornado.web.StaticFileHandler):
    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        if not self.application.auth.is_enabled() and (absolute_path.endswith("/login.html")):
            raise tornado.web.HTTPError(404)

        return super(AuthorizedStaticFileHandler, self).validate_absolute_path(root, absolute_path)


class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        auth = self.application.auth
        if not auth.is_enabled():
            return

        username = self.get_argument("username")
        password = self.get_argument("password")

        auth.authenticate(username, password, self)


class LogoutHandler(tornado.web.RequestHandler):
    @check_authorization
    def post(self):
        auth = self.application.auth

        auth.logout(self)


class GetUsernameHandler(tornado.web.RequestHandler):
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
        logger = logging.getLogger('scriptServer')

        audit_name = get_audit_name(self, logger)

        file_path = file_utils.relative_path(absolute_path, os.path.abspath(root))
        if not file_download_feature.allowed_to_download(file_path, audit_name, get_tornado_secret()):
            logger.warn('Access attempt from ' + audit_name + ' to ' + absolute_path)
            raise tornado.web.HTTPError(404)

        return super(AuthorizedStaticFileHandler, self).validate_absolute_path(root, absolute_path)


def respond_error(request_handler, status_code, message):
    request_handler.set_status(status_code)
    request_handler.write(message)


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


def pipe_process_to_http(process_wrapper: execution.ProcessWrapper, log_identifier, write_callback):
    script_logger = logging.getLogger("scriptServer")

    try:
        log_file = open(os.path.join("logs", "processes", log_identifier + ".log"), "w")
    except:
        log_file = None
        script_logger.exception("Couldn't create a log file")

    try:
        bash_formatting = process_wrapper.get_config().is_bash_formatting()

        reader = None
        if bash_formatting:
            reader = bash_utils.BashReader()

        while True:
            process_output = process_wrapper.read()

            try:
                if log_file and (process_output is not None):
                    log_file.write(process_output)
                    log_file.flush()
            except:
                script_logger.exception("Couldn't write to the log file")

            if process_output is not None:
                if reader:
                    read_iterator = reader.read(process_output)
                    for text in read_iterator:
                        write_callback(wrap_script_output(
                            text.text,
                            text.text_color,
                            text.background_color,
                            text.styles
                        ))

                else:
                    write_callback(wrap_script_output(process_output))

            elif process_wrapper.is_finished():
                if reader:
                    remaining_text = reader.get_current_text()
                    if remaining_text:
                        write_callback(wrap_script_output(
                            remaining_text.text,
                            remaining_text.text_color,
                            remaining_text.background_color,
                            remaining_text.styles
                        ))

                break
    finally:
        try:
            if log_file:
                log_file.close()
        except:
            script_logger.exception("Couldn't close the log file")


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
    with open("logging.json", "rt") as f:
        log_config = json.load(f)
        file_utils.prepare_folder(os.path.join("logs", "processes"))

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

    auth = TornadoAuth(server_config.authorizer)

    result_files_folder = file_download_feature.get_result_files_folder(TEMP_FOLDER)
    file_download_feature.autoclean_downloads(TEMP_FOLDER)

    handlers = [(r"/scripts/list", GetScripts),
                (r"/scripts/info", GetScriptInfo),
                (r"/scripts/execute", ScriptExecute),
                (r"/scripts/execute/stop", ScriptStop),
                (r"/scripts/execute/io/(.*)", ScriptStreamsSocket),
                (r'/' + file_download_feature.RESULT_FILES_FOLDER + '/(.*)',
                 DownloadResultFile,
                 {'path': result_files_folder}),
                (r"/", tornado.web.RedirectHandler, {"url": "/index.html"})]

    if auth.is_enabled():
        handlers.append((r"/login", LoginHandler))
        handlers.append((r"/logout", LogoutHandler))

    handlers.append((r"/username", GetUsernameHandler))

    handlers.append((r"/(.*)", AuthorizedStaticFileHandler, {"path": "web"}))

    application = tornado.web.Application(handlers, **settings)

    application.auth = auth

    application.alerts_config = server_config.get_alerts_config()

    http_server = httpserver.HTTPServer(application, ssl_options=ssl_context)
    http_server.listen(server_config.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
