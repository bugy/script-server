# noinspection PyBroadException
import logging
import os
import re
from string import Template
from typing import Optional

from auth.authorization import is_same_user
from execution.execution_service import ExecutionService
from model import model_helper
from model.model_helper import AccessProhibitedException
from model.server_conf import LoggingConfig
from utils import file_utils, audit_utils
from utils.audit_utils import get_audit_name
from utils.collection_utils import get_first_existing
from utils.date_utils import get_current_millis, ms_to_datetime

ENCODING = 'utf8'

OUTPUT_STARTED_MARKER = '>>>>>  OUTPUT STARTED <<<<<'

LOGGER = logging.getLogger('script_server.execution.logging')


class ScriptOutputLogger:
    def __init__(self, log_file_path, output_stream):
        self.opened = False
        self.closed = False
        self.output_stream = output_stream

        self.log_file_path = log_file_path
        self.log_file = None
        self.close_callback = None

    def start(self):
        self._ensure_file_open()

        self.output_stream.subscribe(self)

    def _ensure_file_open(self):
        if self.opened:
            return

        try:
            self.log_file = open(self.log_file_path, 'wb')
        except:
            LOGGER.exception("Couldn't create a log file")

        self.opened = True

    def __log(self, text):
        if not self.opened:
            LOGGER.exception('Attempt to write to not opened logger')
            return

        if not self.log_file:
            return

        try:
            if text is not None:
                self.log_file.write(text.encode(ENCODING))
                self.log_file.flush()
        except:
            LOGGER.exception("Couldn't write to the log file")

    def _close(self):
        try:
            if self.log_file:
                self.log_file.close()
        except:
            LOGGER.exception("Couldn't close the log file")

        self.closed = True

        if self.close_callback:
            self.close_callback()

    def on_next(self, output):
        self.__log(output)

    def on_close(self):
        self._close()

    def write_line(self, text):
        self._ensure_file_open()

        self.__log(text + os.linesep)

    def set_close_callback(self, callback):
        if self.close_callback is not None:
            LOGGER.error('Attempt to override close callback ' + repr(self.close_callback) + ' with ' + repr(callback))
            return

        self.close_callback = callback

        if self.closed:
            self.close_callback()


class HistoryEntry:
    def __init__(self):
        self.user_name = None
        self.user_id = None
        self.start_time = None
        self.script_name = None
        self.command = None
        self.output_format = None
        self.id = None
        self.exit_code = None


class ExecutionLoggingService:
    def __init__(self, output_folder, log_name_creator, authorizer):
        self._output_folder = output_folder
        self._log_name_creator = log_name_creator
        self._authorizer = authorizer

        self._visited_files = set()
        self._ids_to_file_map = {}
        self._output_loggers = {}

        file_utils.prepare_folder(output_folder)

        self._renew_files_cache()

    def start_logging(self, execution_id,
                      user_name,
                      user_id,
                      command,
                      output_stream,
                      all_audit_names,
                      script_config,
                      parameter_values,
                      start_time_millis=None):

        script_name = str(script_config.name)

        if start_time_millis is None:
            start_time_millis = get_current_millis()

        log_filename = self._log_name_creator.create_filename(
            execution_id,
            all_audit_names,
            script_name,
            start_time_millis,
            script_config.logging_config,
            script_config.parameters,
            parameter_values)
        log_file_path = os.path.join(self._output_folder, log_filename)
        log_file_path = file_utils.create_unique_filename(log_file_path)

        output_logger = ScriptOutputLogger(log_file_path, output_stream)
        output_logger.write_line('id:' + execution_id)
        output_logger.write_line('user_name:' + user_name)
        output_logger.write_line('user_id:' + user_id)
        output_logger.write_line('script:' + script_name)
        output_logger.write_line('start_time:' + str(start_time_millis))
        output_logger.write_line('command:' + command)
        output_logger.write_line('output_format:' + script_config.output_format)
        output_logger.write_line(OUTPUT_STARTED_MARKER)
        output_logger.start()

        log_filename = os.path.basename(log_file_path)
        self._visited_files.add(log_filename)
        self._ids_to_file_map[execution_id] = log_filename
        self._output_loggers[execution_id] = output_logger

    def write_post_execution_info(self, execution_id, exit_code):
        filename = self._ids_to_file_map.get(execution_id)
        if not filename:
            LOGGER.warning('Failed to find filename for execution ' + execution_id)
            return

        logger = self._output_loggers.get(execution_id)
        if not logger:
            LOGGER.warning('Failed to find logger for execution ' + execution_id)
            return

        log_file_path = os.path.join(self._output_folder, filename)

        logger.set_close_callback(lambda: self._write_post_execution_info(log_file_path, exit_code))

    def get_history_entries(self, user_id, *, system_call=False):
        self._renew_files_cache()

        result = []

        for file in self._ids_to_file_map.values():
            history_entry = self._extract_history_entry(file)
            if history_entry is not None and self._can_access_entry(history_entry, user_id, system_call):
                result.append(history_entry)

        return result

    def find_history_entry(self, execution_id, user_id):
        self._renew_files_cache()

        file = self._ids_to_file_map.get(execution_id)
        if file is None:
            LOGGER.warning('find_history_entry: file for %s id not found', execution_id)
            return None

        entry = self._extract_history_entry(file)
        if entry is None:
            LOGGER.warning('find_history_entry: cannot parse file for %s', execution_id)

        elif not self._can_access_entry(entry, user_id):
            message = 'User ' + user_id + ' has no access to execution #' + str(execution_id)
            LOGGER.warning('%s. Original user: %s', message, entry.user_id)
            raise AccessProhibitedException(message)

        return entry

    def find_log(self, execution_id):
        self._renew_files_cache()

        file = self._ids_to_file_map.get(execution_id)
        if file is None:
            LOGGER.warning('find_log: file for %s id not found', execution_id)
            return None

        file_content = file_utils.read_file(os.path.join(self._output_folder, file),
                                            keep_newlines=True)
        log = file_content.split(OUTPUT_STARTED_MARKER, 1)[1]
        return _lstrip_any_linesep(log)

    def _extract_history_entry(self, file):
        file_path = os.path.join(self._output_folder, file)
        correct_format, parameters_text = self._read_parameters_text(file_path)
        if not correct_format:
            return None
        parameters = self._parse_history_parameters(parameters_text)
        return self._parameters_to_entry(parameters)

    @staticmethod
    def _read_parameters_text(file_path):
        parameters_text = ''
        correct_format = False
        with open(file_path, 'r', encoding=ENCODING) as f:
            for line in f:
                if _rstrip_once(line, '\n') == OUTPUT_STARTED_MARKER:
                    correct_format = True
                    break
                parameters_text += line
        return correct_format, parameters_text

    def _renew_files_cache(self):
        cache = self._ids_to_file_map

        obsolete_ids = []
        for id, file in cache.items():
            path = os.path.join(self._output_folder, file)
            if not os.path.exists(path):
                obsolete_ids.append(id)

        for obsolete_id in obsolete_ids:
            LOGGER.info('Logs for execution #' + obsolete_id + ' were deleted')
            del cache[obsolete_id]

        for file in os.listdir(self._output_folder):
            if not file.lower().endswith('.log'):
                continue

            if file in self._visited_files:
                continue

            self._visited_files.add(file)

            entry = self._extract_history_entry(file)
            if entry is None:
                continue

            cache[entry.id] = file

    @staticmethod
    def _create_log_identifier(audit_name, script_name, start_time):
        audit_name = file_utils.to_filename(audit_name)

        date_string = ms_to_datetime(start_time).strftime("%y%m%d_%H%M%S")

        script_name = script_name.replace(" ", "_")
        log_identifier = script_name + "_" + audit_name + "_" + date_string
        return log_identifier

    @staticmethod
    def _parse_history_parameters(parameters_text):
        current_value = None
        current_key = None

        parameters = {}
        for line in parameters_text.splitlines(keepends=True):
            match = re.fullmatch('([\w_]+):(.*\r?\n)', line)
            if not match:
                current_value += line
                continue

            if current_key is not None:
                parameters[current_key] = _rstrip_once(current_value, '\n')

            current_key = match.group(1)
            current_value = match.group(2)

        if current_key is not None:
            parameters[current_key] = _rstrip_once(current_value, '\n')

        return parameters

    @staticmethod
    def _parameters_to_entry(parameters):
        id = parameters.get('id')
        if not id:
            return None

        entry = HistoryEntry()
        entry.id = id
        entry.script_name = parameters.get('script')
        entry.user_name = parameters.get('user_name')
        entry.user_id = parameters.get('user_id')
        entry.command = parameters.get('command')
        entry.output_format = parameters.get('output_format')

        exit_code = parameters.get('exit_code')
        if exit_code is not None:
            entry.exit_code = int(exit_code)

        start_time = parameters.get('start_time')
        if start_time:
            entry.start_time = ms_to_datetime(int(start_time))

        return entry

    @staticmethod
    def _write_post_execution_info(log_file_path, exit_code):
        file_content = file_utils.read_file(log_file_path, keep_newlines=True)

        file_parts = file_content.split(OUTPUT_STARTED_MARKER + os.linesep, 1)
        parameters_text = file_parts[0]
        parameters_text += 'exit_code:' + str(exit_code) + os.linesep

        new_content = parameters_text + OUTPUT_STARTED_MARKER + os.linesep + file_parts[1]
        file_utils.write_file(log_file_path, new_content.encode(ENCODING), byte_content=True)

    def _can_access_entry(self, entry, user_id, system_call=False):
        if entry is None:
            return True

        if is_same_user(entry.user_id, user_id):
            return True

        if system_call:
            return True

        return self._authorizer.has_full_history_access(user_id)


class LogNameCreator:
    def __init__(self, filename_pattern=None, date_format=None) -> None:
        self._date_format = date_format if date_format else '%y%m%d_%H%M%S'
        if not filename_pattern:
            filename_pattern = '${SCRIPT}_${AUDIT_NAME}_${DATE}'
        self._filename_template = Template(filename_pattern)

    def create_filename(self,
                        execution_id,
                        all_audit_names,
                        script_name,
                        start_time,
                        custom_logging_config: Optional[LoggingConfig],
                        parameter_configs,
                        parameter_values):

        audit_name = get_audit_name(all_audit_names)
        audit_name = file_utils.to_filename(audit_name)

        date_string = ms_to_datetime(start_time).strftime(self._resolve_date_format(custom_logging_config))

        username = audit_utils.get_audit_username(all_audit_names)

        mapping = {
            'ID': execution_id,
            'USERNAME': username,
            'HOSTNAME': get_first_existing(all_audit_names, audit_utils.PROXIED_HOSTNAME, audit_utils.HOSTNAME,
                                           default='unknown-host'),
            'IP': get_first_existing(all_audit_names, audit_utils.PROXIED_IP, audit_utils.IP),
            'DATE': date_string,
            'AUDIT_NAME': audit_name,
            'SCRIPT': script_name
        }

        filename = self._resolve_filename_template(custom_logging_config).safe_substitute(mapping)
        filename = model_helper.fill_parameter_values(parameter_configs, filename, parameter_values)
        if not filename.lower().endswith('.log'):
            filename += '.log'

        filename = filename.replace(" ", "_").replace("/", "_")

        return filename

    def _resolve_date_format(self, custom_logging_config: Optional[LoggingConfig]):
        if custom_logging_config and custom_logging_config.date_format:
            return custom_logging_config.date_format
        return self._date_format

    def _resolve_filename_template(self, custom_logging_config: Optional[LoggingConfig]):
        if custom_logging_config and custom_logging_config.filename_pattern:
            return Template(custom_logging_config.filename_pattern)
        return self._filename_template


class ExecutionLoggingController:
    def __init__(self, execution_service: ExecutionService, execution_logging_service):
        self._execution_logging_service = execution_logging_service
        self._execution_service = execution_service

    def start(self):
        execution_service = self._execution_service
        logging_service = self._execution_logging_service

        def started(execution_id, user):
            script_config = execution_service.get_config(execution_id, user)
            audit_name = user.get_audit_name()
            owner = user.user_id
            all_audit_names = user.audit_names
            output_stream = execution_service.get_anonymized_output_stream(execution_id)
            audit_command = execution_service.get_audit_command(execution_id)
            parameter_values = execution_service.get_user_parameter_values(execution_id)

            logging_service.start_logging(
                execution_id,
                audit_name,
                owner,
                audit_command,
                output_stream,
                all_audit_names,
                script_config,
                parameter_values)

        def finished(execution_id, user):
            exit_code = execution_service.get_exit_code(execution_id)
            logging_service.write_post_execution_info(execution_id, exit_code)

        self._execution_service.add_start_listener(started)
        self._execution_service.add_finish_listener(finished)


def _rstrip_once(text, char):
    if text.endswith(char):
        text = text[:-1]

    return text


def _lstrip_any_linesep(text):
    if text.startswith('\r\n'):
        return text[2:]

    if text.startswith(os.linesep):
        return text[len(os.linesep):]

    return text
