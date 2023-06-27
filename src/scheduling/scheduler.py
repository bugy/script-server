import logging
import sched
import threading
import time
from datetime import timedelta

from utils import date_utils

_sleep = time.sleep

LOGGER = logging.getLogger('script_server.scheduling.scheduler')


class Scheduler:
    def __init__(self) -> None:
        self.stopped = False

        self.scheduler = sched.scheduler(timefunc=time.time)
        self._start_scheduler()

    def _start_scheduler(self):
        def scheduler_loop():
            while not self.stopped:
                try:
                    self.scheduler.run(blocking=False)
                except:
                    LOGGER.exception('Failed to execute scheduled job')

                now = date_utils.now()
                sleep_delta = timedelta(seconds=1) - timedelta(microseconds=now.microsecond)
                _sleep(sleep_delta.total_seconds())

        self.scheduling_thread = threading.Thread(daemon=True, target=scheduler_loop)
        self.scheduling_thread.start()

    def stop(self):
        self.stopped = True

        def stopper():
            pass

        # just schedule the next execution to exit thread immediately
        self.scheduler.enter(1, 0, stopper)

        self.scheduling_thread.join(1)

    def schedule(self, execute_at_datetime, callback, params):
        self.scheduler.enterabs(execute_at_datetime.timestamp(), 1, callback, params)
