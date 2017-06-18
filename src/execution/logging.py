import re

from model import model_helper


# noinspection PyBroadException
class ScriptOutputLogger(object):
    def __init__(self, log_file_path, logger, script_config, execution_info):
        self.logger = logger
        self.opened = False

        self.log_file_path = log_file_path
        self.log_file = None

        self.execution_info = execution_info
        self.script_config = script_config

        self.word_replacements = {}
        for parameter in script_config.parameters:
            if not parameter.secure:
                continue

            value = execution_info.param_values[parameter.name]
            if (value is None) or (value == ''):
                continue

            value_string = str(value)
            if not value_string.strip():
                continue

            value_pattern = '\\b' + re.escape(value_string) + '\\b'
            self.word_replacements[value_pattern] = model_helper.SECURE_MASK

    def open(self):
        try:
            self.log_file = open(self.log_file_path, 'w')
        except:
            self.logger.exception("Couldn't create a log file")

        self.opened = True

    def log(self, process_output):
        if not self.opened:
            self.logger.exception('Attempt to write to not opened logger')
            return

        if not self.log_file:
            return

        try:
            if process_output is not None:
                loggable_output = secure_output(process_output, self.word_replacements)

                self.log_file.write(loggable_output)
                self.log_file.flush()
        except:
            self.logger.exception("Couldn't write to the log file")

    def close(self):
        try:
            if self.log_file:
                self.log_file.close()
        except:
            self.logger.exception("Couldn't close the log file")


def secure_output(process_output, word_replacements):
    result = process_output

    if word_replacements:
        for word, replacement in word_replacements.items():
            result = re.sub(word, replacement, result)

    return result
