import queue
import threading

import time


class ProcessWrapper(object):
    process = None
    output = queue.Queue()

    def __init__(self, process):
        self.process = process

        read_output_thread = threading.Thread(target=self.pipe_process_output, args=())
        read_output_thread.start()

    def write_to_input(self, value):
        input_value = value + "\n"

        self.output.put(input_value)

        self.process.stdin.write(input_value.encode())
        self.process.stdin.flush()

    def get_process_id(self):
        return self.process.pid

    def is_finished(self):
        return self.process.poll() is not None

    def stop(self):
        if not self.is_finished():
            self.output.put(">> STOPPED BY USER")
            self.process.kill()

    def read(self):
        while True:
            try:
                result = self.output.get(0.1)
                return result
            except queue.Empty:
                if self.is_finished():
                    break

    def pipe_process_output(self):
        empty_count = 0

        while True:
            line_bytes = self.process.stdout.readline()

            if not line_bytes:
                empty_count += 1

                if self.is_finished():
                    break

                time.sleep(min(0.3, 0.03 * empty_count))

            else:
                line = line_bytes.decode("UTF-8")
                self.output.put(line)
