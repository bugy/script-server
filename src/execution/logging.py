# noinspection PyBroadException
import logging

LOGGER = logging.getLogger('script_server.ScriptOutputLogger')


class ScriptOutputLogger(object):
    def __init__(self, log_file_path, output_stream):
        self.opened = False
        self.output_stream = output_stream

        self.log_file_path = log_file_path
        self.log_file = None

    def start(self):
        try:
            self.log_file = open(self.log_file_path, 'w')
        except:
            LOGGER.exception("Couldn't create a log file")

        self.opened = True

        self.output_stream.subscribe(self)

    def __log(self, process_output):
        if not self.opened:
            LOGGER.exception('Attempt to write to not opened logger')
            return

        if not self.log_file:
            return

        try:
            if process_output is not None:
                self.log_file.write(process_output)
                self.log_file.flush()
        except:
            LOGGER.exception("Couldn't write to the log file")

    def _close(self):
        try:
            if self.log_file:
                self.log_file.close()
        except:
            LOGGER.exception("Couldn't close the log file")

    def on_next(self, output):
        self.__log(output)

    def on_close(self):
        self._close()
