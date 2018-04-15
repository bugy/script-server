# noinspection PyBroadException
import abc
import logging
import os
import re
from datetime import datetime

from utils import file_utils
from utils.date_utils import get_current_millis, ms_to_datetime, sec_to_datetime, to_millis

OUTPUT_STARTED_MARKER = '>>>>>  OUTPUT STARTED <<<<<'

LOGGER = logging.getLogger('script_server.execution.logging')


class ScriptOutputLogger:
    def __init__(self, log_file_path, output_stream, on_close_callback=None):
        self.opened = False
        self.output_stream = output_stream

        self.log_file_path = log_file_path
        self.log_file = None
        self.on_close_callback = on_close_callback

    def start(self):
        self._ensure_file_open()

        self.output_stream.subscribe(self)

    def _ensure_file_open(self):
        if self.opened:
            return

        try:
            self.log_file = open(self.log_file_path, 'w')
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
                self.log_file.write(text)
                self.log_file.flush()
        except:
            LOGGER.exception("Couldn't write to the log file")

    def _close(self):
        try:
            if self.log_file:
                self.log_file.close()
        except:
            LOGGER.exception("Couldn't close the log file")

        if self.on_close_callback is not None:
            self.on_close_callback()

    def on_next(self, output):
        self.__log(output)

    def on_close(self):
        self._close()

    def write_line(self, text):
        self._ensure_file_open()

        self.__log(text + '\n')


class HistoryEntry:
    def __init__(self):
        self.username = None
        self.start_time = None
        self.script_name = None
        self.command = None
        self.id = None
        self.exit_code = None


class PostExecutionInfoProvider(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_exit_code(self, execution_id):
        pass


class ExecutionLoggingService:
    def __init__(self, output_folder):
        self._output_folder = output_folder

        self._visited_files = set()
        self._ids_to_file_map = {}

        file_utils.prepare_folder(output_folder)

        self._renew_files_cache()
        self.__migrate_old_files(output_folder)

    def start_logging(self, execution_id, username, script_name,
                      command,
                      output_stream,
                      post_execution_info_provider,
                      start_time_millis=None):

        if start_time_millis is None:
            start_time_millis = get_current_millis()

        log_identifier = self._create_log_identifier(username, script_name, start_time_millis)
        log_file_path = os.path.join(self._output_folder, log_identifier + '.log')
        log_file_path = file_utils.create_unique_filename(log_file_path)

        def write_post_execution_info():
            self._write_post_execution_info(execution_id, log_file_path, post_execution_info_provider)

        output_logger = ScriptOutputLogger(log_file_path, output_stream, write_post_execution_info)
        output_logger.write_line('id:' + execution_id)
        output_logger.write_line('user:' + username)
        output_logger.write_line('script:' + script_name)
        output_logger.write_line('start_time:' + str(start_time_millis))
        output_logger.write_line('command:' + command)
        output_logger.write_line(OUTPUT_STARTED_MARKER)
        output_logger.start()

        log_filename = os.path.basename(log_file_path)
        self._visited_files.add(log_filename)
        self._ids_to_file_map[execution_id] = log_filename

    def get_history_entries(self):
        self._renew_files_cache()

        result = []

        for file in self._ids_to_file_map.values():
            history_entry = self._extract_history_entry(file)
            if history_entry is not None:
                result.append(history_entry)

        return result

    def find_history_entry(self, execution_id):
        self._renew_files_cache()

        file = self._ids_to_file_map.get(execution_id)
        if file is None:
            LOGGER.warning('find_history_entry: file for %s id not found', execution_id)
            return None

        entry = self._extract_history_entry(file)
        if entry is None:
            LOGGER.warning('find_history_entry: cannot parse file for %s', execution_id)

        return entry

    def find_log(self, execution_id):
        self._renew_files_cache()

        file = self._ids_to_file_map.get(execution_id)
        if file is None:
            LOGGER.warning('find_log: file for %s id not found', execution_id)
            return None

        file_content = file_utils.read_file(os.path.join(self._output_folder, file))
        log = file_content.split(OUTPUT_STARTED_MARKER + '\n', 1)[1]
        return log

    def _extract_history_entry(self, file):
        file_path = os.path.join(self._output_folder, file)
        correct_format, parameters_text = self._read_parameters_text(file_path)
        if not correct_format:
            return None
        history_entry = self._parse_history_parameters(parameters_text, file_path)
        return history_entry

    @staticmethod
    def _read_parameters_text(file_path):
        parameters_text = ''
        correct_format = False
        with open(file_path, 'r') as f:
            for line in f:
                if line.rstrip('\n') == OUTPUT_STARTED_MARKER:
                    correct_format = True
                    break
                parameters_text += line
        return correct_format, parameters_text

    def _renew_files_cache(self):
        for file in os.listdir(self._output_folder):
            if not file.lower().endswith('.log'):
                continue

            if file in self._visited_files:
                continue

            self._visited_files.add(file)

            entry = self._extract_history_entry(file)
            if entry is None:
                continue

            self._ids_to_file_map[entry.id] = file

    @staticmethod
    def _create_log_identifier(audit_name, script_name, start_time):
        audit_name = file_utils.to_filename(audit_name)

        date_string = ms_to_datetime(start_time).strftime("%y%m%d_%H%M%S")

        script_name = script_name.replace(" ", "_")
        log_identifier = script_name + "_" + audit_name + "_" + date_string
        return log_identifier

    @staticmethod
    def _parse_history_parameters(parameters_text, file_path):
        current_value = None
        current_key = None

        parameters = {}
        for line in parameters_text.splitlines(keepends=True):
            match = re.fullmatch('([\w_]+):(.*\r?\n)', line)
            if not match:
                current_value += line
                continue

            if current_key is not None:
                parameters[current_key] = current_value.rstrip('\n')

            current_key = match.group(1)
            current_value = match.group(2)

        if current_key is not None:
            parameters[current_key] = current_value.rstrip('\n')

        id = parameters.get('id')
        if not id:
            return None

        entry = HistoryEntry()
        entry.id = id
        entry.script_name = parameters.get('script')
        entry.username = parameters.get('user')
        entry.command = parameters.get('command')

        exit_code = parameters.get('exit_code')
        if exit_code is not None:
            entry.exit_code = int(exit_code)

        start_time = parameters.get('start_time')
        if start_time:
            entry.start_time = ms_to_datetime(int(start_time))

        return entry

    def __migrate_old_files(self, output_folder):
        log_files = [os.path.join(output_folder, file)
                     for file in os.listdir(output_folder)
                     if file.lower().endswith('.log')]

        # from oldest to newest
        log_files.sort(key=lambda file_path: file_path[-17:])

        def is_new_format(log_file):
            with open(log_file, 'r') as f:
                first_line = f.readline().strip()

                if not first_line.startswith('id:'):
                    return False

                for line in f:
                    if line.strip() == OUTPUT_STARTED_MARKER:
                        return True

            return False

        old_files = []
        for log_file in log_files:
            if is_new_format(log_file):
                break
            old_files.append(log_file)

        if not old_files:
            return

        used_ids = set(self._ids_to_file_map.keys())

        def id_generator_function():
            counter = 0
            while True:
                id = str(counter)
                if id not in used_ids:
                    yield id

                counter += 1

        id_generator = id_generator_function()

        for old_file in old_files:
            log_basename = os.path.basename(old_file)
            filename = os.path.splitext(log_basename)[0]

            match = re.fullmatch('(.+)_([^_]+)_((\d\d)(\d\d)(\d\d)_(\d\d)(\d\d)(\d\d))', filename)
            if match:
                script_name = match.group(1)
                username = match.group(2)
                start_time = datetime.strptime(match.group(3), '%y%m%d_%H%M%S')
                id = next(id_generator)
            else:
                script_name = 'unknown'
                username = 'unknown'
                start_time = sec_to_datetime(os.path.getctime(old_file))
                id = next(id_generator)

            new_begin = ''
            new_begin += 'id:' + id + '\n'
            new_begin += 'user:' + username + '\n'
            new_begin += 'script:' + script_name + '\n'
            new_begin += 'start_time:' + str(to_millis(start_time)) + '\n'
            new_begin += 'command:unknown' + '\n'
            new_begin += OUTPUT_STARTED_MARKER + '\n'

            file_content = file_utils.read_file(old_file)
            file_content = new_begin + file_content
            file_utils.write_file(old_file, file_content)

            self._ids_to_file_map[id] = log_basename

    @staticmethod
    def _write_post_execution_info(execution_id, log_file_path, post_execution_info_provider):
        exit_code = post_execution_info_provider.get_exit_code(execution_id)
        if exit_code is None:
            return

        file_content = file_utils.read_file(log_file_path)

        file_parts = file_content.split(OUTPUT_STARTED_MARKER + '\n', 1)
        parameters_text = file_parts[0]
        parameters_text += 'exit_code:' + str(exit_code) + '\n'

        new_content = parameters_text + OUTPUT_STARTED_MARKER + '\n' + file_parts[1]
        file_utils.write_file(log_file_path, new_content)
