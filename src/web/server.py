#!/usr/bin/env python3
import asyncio
import json
import logging.config
import os
import signal
import ssl
import time
import urllib
from urllib.parse import urlencode

import tornado.concurrent
import tornado.escape
import tornado.httpserver as httpserver
import tornado.ioloop
import tornado.routing
import tornado.web
import tornado.websocket

from auth.identification import AuthBasedIdentification, IpBasedIdentification
from auth.tornado_auth import TornadoAuth
from communications.alerts_service import AlertsService
from config.config_service import ConfigService, ConfigNotAllowedException, InvalidAccessException, \
    CorruptConfigFileException
from config.exceptions import InvalidConfigException
from execution.execution_service import ExecutionService
from execution.logging import ExecutionLoggingService
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from model import external_model
from model.external_model import to_short_execution_log, to_long_execution_log
from model.model_helper import is_empty, InvalidFileException, AccessProhibitedException
from model.parameter_config import WrongParameterUsageException
from model.script_config import InvalidValueException, ParameterNotFoundException
from model.server_conf import ServerConfig, XSRF_PROTECTION_TOKEN, XSRF_PROTECTION_DISABLED, XSRF_PROTECTION_HEADER
from scheduling.schedule_service import ScheduleService, UnavailableScriptException, InvalidScheduleException
from utils import file_utils as file_utils
from utils import tornado_utils, os_utils, env_utils, custom_json
from utils.audit_utils import get_audit_name_from_request
from utils.exceptions.missing_arg_exception import MissingArgumentException
from utils.exceptions.not_found_exception import NotFoundException
from utils.tornado_utils import respond_error, redirect_relative, get_form_file
from web.script_config_socket import ScriptConfigSocket, active_config_models
from web.streaming_form_reader import StreamingFormReader
from web.web_auth_utils import check_authorization
from web.web_utils import wrap_to_server_event, identify_user, inject_user, get_user
from web.xheader_app_wrapper import autoapply_xheaders

BYTES_IN_MB = 1024 * 1024

LOGGER = logging.getLogger('web_server')


def requires_admin_rights(func):
    def wrapper(self, *args, **kwargs):
        if not has_admin_rights(self):
            user_id = identify_user(self)
            LOGGER.warning('User %s (%s) tried to access admin REST service %s',
                           user_id, get_audit_name_from_request(self), self.request.path)
            raise tornado.web.HTTPError(403, 'Access denied')

        return func(self, *args, **kwargs)

    return wrapper


def has_admin_rights(request_handler):
    user_id = identify_user(request_handler)
    return request_handler.application.authorizer.is_admin(user_id)


class ProxiedRedirectHandler(tornado.web.RedirectHandler):
    def get(self, *args):
        redirect_relative(self._url.format(*args), self, *args)


def exception_to_code_and_message(exception):
    if isinstance(exception, AccessProhibitedException):
        return 403, str(exception)
    if isinstance(exception, MissingArgumentException):
        return 400, str(exception)
    if isinstance(exception, NotFoundException):
        return 404, str(exception)

    return None, None


class BaseRequestHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')

        if self.application.server_config.xsrf_protection == XSRF_PROTECTION_TOKEN:
            # This is needed to initialize cookie (by default tornado does it only on html template rendering)
            # noinspection PyStatementEffect
            self.xsrf_token

    def check_xsrf_cookie(self):
        xsrf_protection = self.application.server_config.xsrf_protection
        if xsrf_protection == XSRF_PROTECTION_TOKEN:
            return super().check_xsrf_cookie()

        elif xsrf_protection == XSRF_PROTECTION_HEADER:
            requested_with = self.request.headers.get('X-Requested-With')
            if not requested_with:
                raise tornado.web.HTTPError(403, 'X-Requested-With header is missing for XSRF protection')
            return

    def write_error(self, status_code, **kwargs):
        if ('exc_info' in kwargs) and (kwargs['exc_info']):
            (type, value, traceback) = kwargs['exc_info']
            (custom_code, custom_message) = exception_to_code_and_message(value)

            if custom_code:
                respond_error(self, custom_code, custom_message)
                return

        respond_error(self, status_code, self._reason)


class BaseStaticHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('X-Frame-Options', 'DENY')


class GetServerConf(BaseRequestHandler):
    @check_authorization
    def get(self):
        self.write(external_model.server_conf_to_external(
            self.application.server_config,
            self.application.server_version))


class GetScripts(BaseRequestHandler):
    @check_authorization
    @inject_user
    def get(self, user):
        mode = self.get_query_argument('mode', default=None)

        configs = self.application.config_service.list_configs(user, mode)

        scripts = [{'name': conf.name, 'group': conf.group, 'parsing_failed': conf.parsing_failed} for conf in configs]

        self.write(json.dumps({'scripts': scripts}))


class AdminUpdateScriptEndpoint(BaseRequestHandler):
    @requires_admin_rights
    @inject_user
    def post(self, user):
        (config, _, uploaded_script) = self.read_config_parameters()

        try:
            self.application.config_service.create_config(user, config, uploaded_script)
        except InvalidConfigException as e:
            logging.warning('Failed to create script config', exc_info=True)
            raise tornado.web.HTTPError(422, reason=str(e))
        except InvalidAccessException as e:
            logging.warning('Failed to create script config', exc_info=True)
            raise tornado.web.HTTPError(403, reason=str(e))

    @requires_admin_rights
    @inject_user
    def put(self, user):
        (config, filename, uploaded_script) = self.read_config_parameters()

        try:
            self.application.config_service.update_config(user, config, filename, uploaded_script)
        except (InvalidConfigException, InvalidFileException) as e:
            raise tornado.web.HTTPError(422, str(e))
        except ConfigNotAllowedException:
            LOGGER.warning('Admin access to the script "' + config['name'] + '" is denied for ' + user.get_audit_name())
            respond_error(self, 403, 'Access to the script is denied')
            return
        except InvalidAccessException as e:
            raise tornado.web.HTTPError(403, reason=str(e))

    def read_config_parameters(self):
        config = json.loads(self.get_argument('config'))
        filename = self.get_argument('filename', default=None)
        uploaded_script = get_form_file(self, 'uploadedScript')

        return config, filename, uploaded_script


class AdminScriptEndpoint(BaseRequestHandler):
    @requires_admin_rights
    @inject_user
    def get(self, user, script_name):
        try:
            config = self.application.config_service.load_config(script_name, user)
        except ConfigNotAllowedException:
            LOGGER.warning('Admin access to the script "' + script_name + '" is denied for ' + user.get_audit_name())
            respond_error(self, 403, 'Access to the script is denied')
            return
        except CorruptConfigFileException as e:
            respond_error(self, CorruptConfigFileException.HTTP_CODE, str(e))
            return

        if config is None:
            raise tornado.web.HTTPError(404, str('Failed to find config for name: ' + script_name))

        self.write(json.dumps(config))

    @requires_admin_rights
    @inject_user
    def delete(self, user, script_name):
        try:
            self.application.config_service.delete_config(user, script_name)
        except ConfigNotAllowedException:
            LOGGER.warning(
                f'Admin access to the script "{script_name}" is denied for {user.get_audit_name()}'
            )
            respond_error(self, 403, 'Access to the script is denied')
            return
        except NotFoundException as e:
            LOGGER.warning(f'Failed to delete script {script_name}', exc_info=True)
            respond_error(self, 404, str(e))
            return
        except InvalidAccessException as e:
            raise tornado.web.HTTPError(403, reason=str(e)) from e


class AdminGetScriptCodeEndpoint(BaseRequestHandler):
    @requires_admin_rights
    @inject_user
    def get(self, user, script_name):
        try:
            loaded_script = self.application.config_service.load_script_code(script_name, user)
        except ConfigNotAllowedException:
            LOGGER.warning('Admin access to the script "' + script_name + '" is denied for ' + user.get_audit_name())
            respond_error(self, 403, 'Access to the script is denied')
            return
        except InvalidFileException as e:
            LOGGER.warning('Failed to load script code for script ' + script_name, exc_info=True)
            respond_error(self, 422, str(e))
            return
        except InvalidAccessException as e:
            raise tornado.web.HTTPError(403, reason=str(e))

        if loaded_script is None:
            raise tornado.web.HTTPError(404, str('Failed to find config for name: ' + script_name))

        self.write(json.dumps(loaded_script))


class ScriptStop(BaseRequestHandler):
    @check_authorization
    @inject_user
    def post(self, user, execution_id):
        self.application.execution_service.stop_script(execution_id, user)


class ScriptKill(BaseRequestHandler):
    @check_authorization
    @inject_user
    def post(self, user, execution_id):
        self.application.execution_service.kill_script(execution_id, user)


class ScriptStreamSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.executor = None

    @check_authorization
    @inject_user
    def open(self, user, execution_id):
        auth = self.application.auth
        if not auth.is_authenticated(self):
            return None

        execution_service = self.application.execution_service

        try:
            self.executor = execution_service.get_active_executor(execution_id, get_user(self))
        except Exception as e:
            self.handle_exception_on_open(e)
            return

        self.ioloop = tornado.ioloop.IOLoop.current()

        self.write_message(wrap_to_server_event('input', 'your input >>'))

        user_id = identify_user(self)

        output_stream = execution_service.get_raw_output_stream(execution_id, user_id)
        pipe_output_to_http(output_stream, self.safe_write)

        file_download_feature = self.application.file_download_feature
        web_socket = self

        def finished():
            try:
                downloadable_files = file_download_feature.get_downloadable_files(execution_id)

                for file in downloadable_files:
                    filename = os.path.basename(file)
                    url_path = web_socket.prepare_download_url(file)

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

        file_download_feature.subscribe_on_inline_images(execution_id, self.send_inline_image)

        execution_service.add_finish_listener(finished, execution_id)

    def on_message(self, text):
        self.executor.write_to_input(text)

    def on_close(self):
        audit_name = get_audit_name_from_request(self)
        LOGGER.info(audit_name + ' disconnected')

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.ioloop.add_callback(self.write_message, message)

    def send_inline_image(self, original_path, download_path):
        self.safe_write(wrap_to_server_event(
            'inline-image',
            {'output_path': original_path, 'download_url': self.prepare_download_url(download_path)}))

    def prepare_download_url(self, file):
        downloads_folder = self.application.downloads_folder
        relative_path = file_utils.relative_path(file, downloads_folder)

        filename = tornado.escape.url_escape(os.path.basename(relative_path))
        relative_dir = os.path.dirname(relative_path).replace(os.path.sep, '/')

        url_path = relative_dir + '/' + filename

        return 'result_files/' + url_path

    def handle_exception_on_open(self, e):
        (status_code, message) = exception_to_code_and_message(e)
        if status_code:
            self.close(code=status_code, reason=message)
            return
        raise e


@tornado.web.stream_request_body
class StreamUploadRequestHandler(BaseRequestHandler):
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


class ScriptExecute(StreamUploadRequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    @inject_user
    def post(self, user):
        script_name = None

        audit_name = user.get_audit_name()

        try:
            arguments = self.form_reader.values
            execution_info = external_model.to_execution_info(arguments)

            script_name = execution_info.script

            config_model = self.application.config_service.load_config_model(script_name, user)

            if not config_model:
                message = 'Script with name "' + str(script_name) + '" not found'
                LOGGER.error(message)
                respond_error(self, 400, message)
                return

            parameter_values = execution_info.param_values

            if self.form_reader.files:
                for key, value in self.form_reader.files.items():
                    parameter_values[key] = value.path

            all_audit_names = user.audit_names
            LOGGER.info('Calling script %s. User %s', script_name, all_audit_names)

            config_model.set_all_param_values(parameter_values)

            execution_id = self.application.execution_service.start_script(config_model, user)

            self.write(str(execution_id))

        except InvalidValueException as e:
            message = 'Invalid parameter %s value: %s' % (e.param_name, str(e))
            LOGGER.error(message)
            respond_error(self, 422, message)
            return

        except ConfigNotAllowedException:
            LOGGER.warning('Access to the script "' + script_name + '" is denied for ' + audit_name)
            respond_error(self, 403, 'Access to the script is denied')
            return

        except CorruptConfigFileException as e:
            respond_error(self, CorruptConfigFileException.HTTP_CODE, str(e))
            return None

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
        user_id = identify_user(self)
        execution_service = self.application.execution_service

        active_executions = execution_service.get_active_executions(user_id)

        self.write(json.dumps(active_executions))


class GetExecutingScriptConfig(BaseRequestHandler):
    @check_authorization
    @inject_user
    def get(self, user, execution_id):
        config = self.application.execution_service.get_config(execution_id, user)

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
    @inject_user
    def post(self, user, execution_id):
        self.application.execution_service.cleanup_execution(execution_id, user)


class GetExecutionStatus(BaseRequestHandler):
    @check_authorization
    @inject_user
    def get(self, user, execution_id):
        running = self.application.execution_service.is_running(execution_id, user)
        self.write(external_model.running_flag_to_status(running))


class AuthorizedStaticFileHandler(BaseStaticHandler):
    admin_files = ['admin.html', 'css/admin.css', 'admin.js', 'admin-deps.css']

    @check_authorization
    def validate_absolute_path(self, root, absolute_path):
        if not self.application.auth.is_enabled() and (absolute_path.endswith("/login.html")):
            raise tornado.web.HTTPError(404)

        relative_path = file_utils.relative_path(absolute_path, root)
        if self.is_admin_file(relative_path):
            if not has_admin_rights(self):
                user_id = identify_user(self)
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


class ThemeStaticFileHandler(AuthorizedStaticFileHandler):

    async def get(self, path: str, include_body: bool = True) -> None:
        if path == 'theme.css':
            self.absolute_path = self.get_absolute_path(self.root, path)
            if not os.path.exists(self.absolute_path):
                # if custom theme doesn't exist, return empty body
                return

        return await super().get(path, include_body)


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
    @check_authorization
    @inject_user
    def get(self, user):
        auth = self.application.auth
        authorizer = self.application.authorizer

        username = None
        if auth.is_enabled():
            username = auth.get_username(self)

        try:
            admin_rights = has_admin_rights(self)
        except Exception:
            admin_rights = False

        info = {
            'enabled': auth.is_enabled(),
            'username': username,
            'admin': admin_rights,
            'canEditCode': authorizer.can_edit_code(user.user_id)
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
        user_id = identify_user(self)

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
    @inject_user
    def get(self, user):
        history_entries = self.application.execution_logging_service.get_history_entries(user.user_id)
        running_script_ids = []
        for entry in history_entries:
            if self.application.execution_service.is_running(entry.id, user):
                running_script_ids.append(entry.id)

        short_logs = to_short_execution_log(history_entries, running_script_ids)
        self.write(json.dumps(short_logs))


class GetLongHistoryEntryHandler(BaseRequestHandler):
    @check_authorization
    @inject_user
    def get(self, user, execution_id):
        if is_empty(execution_id):
            respond_error(self, 400, 'Execution id is not specified')
            return

        try:
            history_entry = self.application.execution_logging_service.find_history_entry(execution_id, user.user_id)
        except AccessProhibitedException:
            respond_error(self, 403, 'Access to execution #' + str(execution_id) + ' is prohibited')
            return

        if history_entry is None:
            respond_error(self, 400, 'No history found for id ' + execution_id)
            return

        log = self.application.execution_logging_service.find_log(execution_id)
        if is_empty(log):
            LOGGER.warning('No log found for execution ' + execution_id)

        running = self.application.execution_service.is_running(history_entry.id, user)
        long_log = to_long_execution_log(history_entry, log, running)
        self.write(json.dumps(long_log))


@tornado.web.stream_request_body
class AddSchedule(StreamUploadRequestHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    @inject_user
    def post(self, user):
        arguments = self.form_reader.values
        execution_info = external_model.to_execution_info(arguments)
        parameter_values = execution_info.param_values

        if self.form_reader.files:
            for key, value in self.form_reader.files.items():
                parameter_values[key] = value.path

        schedule_config = custom_json.loads(parameter_values['__schedule_config'])
        del parameter_values['__schedule_config']

        try:
            id = self.application.schedule_service.create_job(
                execution_info.script,
                parameter_values,
                external_model.parse_external_schedule(schedule_config),
                user)
        except (UnavailableScriptException, InvalidScheduleException) as e:
            raise tornado.web.HTTPError(422, reason=str(e))
        except InvalidValueException as e:
            raise tornado.web.HTTPError(422, reason=e.get_user_message())

        self.write(json.dumps({'id': id}))


def pipe_output_to_http(output_stream, write_callback):
    class OutputToHttpListener:
        def on_next(self, output):
            write_callback(wrap_to_server_event('output', output))

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
                        execution_service.kill_script_by_system(id)
                except:
                    LOGGER.exception('Could not kill running scripts, trying to stop the server')

        if can_stop:
            LOGGER.info('Stopping server on interrupt')
            io_loop.add_callback_from_signal(io_loop.stop)

    signal.signal(signal.SIGINT, signal_handler)


_http_server = None


def init(server_config: ServerConfig,
         authenticator,
         authorizer,
         execution_service: ExecutionService,
         schedule_service: ScheduleService,
         execution_logging_service: ExecutionLoggingService,
         config_service: ConfigService,
         alerts_service: AlertsService,
         file_upload_feature: FileUploadFeature,
         file_download_feature: FileDownloadFeature,
         secret,
         server_version,
         conf_folder,
         *,
         start_server=True):
    ssl_context = None
    if server_config.is_ssl():
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(server_config.get_ssl_cert_path(),
                                    server_config.get_ssl_key_path())

    auth = TornadoAuth(authenticator)
    if auth.is_enabled():
        identification = AuthBasedIdentification(auth)
    else:
        identification = IpBasedIdentification(server_config.ip_validator, server_config.user_header_name)

    downloads_folder = file_download_feature.get_result_files_folder()

    handlers = [(r'/conf', GetServerConf),
                (r'/scripts', GetScripts),
                (r'/scripts/([^/]*)', ScriptConfigSocket),
                (r'/scripts/([^/]*)/([^/]*)/list-files', ScriptParameterListFiles),
                (r'/executions/start', ScriptExecute),
                (r'/executions/stop/(.*)', ScriptStop),
                (r'/executions/kill/(.*)', ScriptKill),
                (r'/executions/io/(.*)', ScriptStreamSocket),
                (r'/executions/active', GetActiveExecutionIds),
                (r'/executions/config/(.*)', GetExecutingScriptConfig),
                (r'/executions/cleanup/(.*)', CleanupExecutingScript),
                (r'/executions/status/(.*)', GetExecutionStatus),
                (r'/history/execution_log/short', GetShortHistoryEntriesHandler),
                (r'/history/execution_log/long/(.*)', GetLongHistoryEntryHandler),
                (r'/schedule', AddSchedule),
                (r'/auth/info', AuthInfoHandler),
                (r'/result_files/(.*)',
                 DownloadResultFile,
                 {'path': downloads_folder}),
                (r'/admin/scripts', AdminUpdateScriptEndpoint),
                (r'/admin/scripts/([^/]+)', AdminScriptEndpoint),
                (r'/admin/scripts/([^/]*)/code', AdminGetScriptCodeEndpoint),
                (r"/", ProxiedRedirectHandler, {"url": "/index.html"})]

    if auth.is_enabled():
        handlers.append((r'/login', LoginHandler))
        handlers.append((r'/auth/config', AuthConfigHandler))
        handlers.append((r'/logout', LogoutHandler))

    handlers.append((r'/theme/(.*)', ThemeStaticFileHandler, {'path': os.path.join(conf_folder, 'theme')}))
    handlers.append((r"/(.*)", AuthorizedStaticFileHandler, {"path": "web"}))

    settings = {
        'cookie_secret': secret,
        "login_url": "/login.html",
        'websocket_ping_interval': 30,
        'websocket_ping_timeout': 300,
        'compress_response': True,
        'xsrf_cookies': server_config.xsrf_protection != XSRF_PROTECTION_DISABLED,
    }

    application = tornado.web.Application(handlers, **settings)
    autoapply_xheaders(application)

    application.auth = auth

    application.server_config = server_config
    application.server_version = server_version
    application.authorizer = authorizer
    application.downloads_folder = downloads_folder
    application.file_download_feature = file_download_feature
    application.file_upload_feature = file_upload_feature
    application.execution_service = execution_service
    application.schedule_service = schedule_service
    application.execution_logging_service = execution_logging_service
    application.config_service = config_service
    application.alerts_service = alerts_service
    application.identification = identification
    application.max_request_size_mb = server_config.max_request_size_mb

    if os_utils.is_win() and env_utils.is_min_version('3.8'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    io_loop = tornado.ioloop.IOLoop.current()

    global _http_server
    _http_server = httpserver.HTTPServer(
        application,
        ssl_options=ssl_context,
        max_buffer_size=10 * BYTES_IN_MB)
    _http_server.listen(server_config.port, address=server_config.address)

    intercept_stop_when_running_scripts(io_loop, execution_service)

    http_protocol = 'https' if server_config.ssl else 'http'
    print('Server is running on: %s://%s:%s' % (http_protocol, server_config.address, server_config.port))

    if start_server:
        io_loop.start()
