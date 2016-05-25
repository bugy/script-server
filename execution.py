import queue
import threading

import time


class ProcessWrapper(object):
    process = None
    output = None

    def __init__(self, process):
        self.process = process
        self.output = queue.Queue()

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
        current_millis = lambda: int(round(time.time() * 1000))

        last_send_time = current_millis()
        buffer_flush_wait = 40

        output_buffer = bytearray()
        while True:
            wait_new_output = False
            finished = False

            if self.is_finished():
                read_data = self.process.stdout.read()
                time_to_flush = True
                finished = True

            else:
                read_data = self.process.stdout.readline()
                time_to_flush = True  # temp fix for PROD (last_send_time + buffer_flush_wait) < current_millis()

                if not read_data:
                    wait_new_output = True

            if read_data:
                output_buffer += read_data

            if output_buffer and time_to_flush:
                output_text = output_buffer.decode("UTF-8")
                self.output.put(output_text)

                output_buffer = bytearray()
                last_send_time = current_millis()

            if finished:
                break

            if wait_new_output:
                time.sleep(0.01)
