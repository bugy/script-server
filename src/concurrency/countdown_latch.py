import threading
import time


class CountDownLatch(object):
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()

    def count_down(self):
        with self.lock:
            self.count -= 1
            if self.count <= 0:
                print('count_down: count = ' + str(self.count))
                self.lock.notifyAll()

    def await_latch(self, timeout=None):
        if timeout:
            end_time = time.time() + timeout

            with self.lock:
                while self.count > 0:
                    wait_delta = end_time - time.time()

                    if wait_delta > 0:
                        print('await_latch before wait: count = ' + str(self.count))
                        self.lock.wait(wait_delta)
                        print('await_latch after wait: count = ' + str(self.count))
                    else:
                        raise TimeoutError('Latch await timed out')

            return

        with self.lock:
            while self.count > 0:
                self.lock.wait()
