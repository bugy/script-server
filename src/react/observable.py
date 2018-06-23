import abc
import logging
import threading
import time

from typing import TypeVar, Generic

T = TypeVar('T')

LOGGER = logging.getLogger('script_server.observable')


class ObservableBase(Generic[T], metaclass=abc.ABCMeta):
    def __init__(self):
        self.observers = []
        self.closed = False
        self.close_condition = threading.Condition()

    def push(self, data: T):
        self._push(data)

    def _push(self, data: T):
        self._fire_on_next(data)

    def close(self):
        self._close()

    def _close(self):
        with self.close_condition:
            if self.closed:
                return

            self.closed = True
            self.close_condition.notify_all()

        self._fire_on_close()

        del self.observers[:]

    def subscribe(self, observer):
        if self.closed:
            observer.on_close()
            return

        self.observers.append(observer)

    def subscribe_on_close(self, callback, *args):
        self.subscribe(_CloseSubscriber(callback, *args))

    def unsubscribe(self, observer):
        if self.closed:
            return

        while observer in self.observers:
            self.observers.remove(observer)

    def _fire_on_next(self, data):
        for observer in self.observers:
            try:
                observer.on_next(data)
            except:
                LOGGER.exception('Could not notify on_next, observer ' + str(observer))

    def _fire_on_close(self):
        for observer in self.observers:
            try:
                observer.on_close()
            except:
                LOGGER.exception('Could not notify on_close, observer ' + str(observer))

    def time_buffered(self, period_millis, aggregate_function=None):
        return _TimeBufferedPipe(self, period_millis, aggregate_function)

    def map(self, map_function):
        return _MappedPipe(self, map_function)

    def replay(self):
        return _ReplayPipe(self)

    def wait_close(self, timeout=None):
        if (timeout is not None) and (timeout > 0):
            self._wait_close_timed(timeout)
        else:
            self._wait_close_unlimited()

    def _wait_close_unlimited(self):
        with self.close_condition:
            while not self.closed:
                self.close_condition.wait()

    def _wait_close_timed(self, timeout=None):
        end_time = time.time() + timeout

        with self.close_condition:
            while not self.closed:
                wait_period = end_time - time.time()
                if wait_period <= 0:
                    return

                self.close_condition.wait(wait_period)


class Observable(ObservableBase[T]):
    def __init__(self):
        super().__init__()


class ReplayObservable(ObservableBase[T]):
    def __init__(self):
        super().__init__()
        self.chunks = []

    def _push(self, data: T):
        self.chunks.append(data)
        super()._push(data)

    def subscribe(self, observer):
        for chunk in self.chunks:
            observer.on_next(chunk)

        super().subscribe(observer)

    def dispose(self):
        self._close()
        del self.chunks[:]


class PipedObservable(ObservableBase[T]):
    def __init__(self, source_observable):
        super().__init__()

        self.origin = source_observable

    def push(self, data):
        raise RuntimeError('Piped observable is read-only')

    def close(self):
        raise RuntimeError('Piped observable is read-only')


class _ReplayPipe(ReplayObservable):
    def __init__(self, source_observable):
        super().__init__()
        self.source = source_observable
        self.source.subscribe(self)

    def push(self, data: T):
        raise RuntimeError('Piped observable is read-only')

    def close(self):
        raise RuntimeError('Piped observable is read-only')

    def on_next(self, data):
        self._push(data)

    def on_close(self):
        self._close()

    def dispose(self):
        self.source.subscribe_on_close(self._defer_dispose)

    def _defer_dispose(self):
        self.source.unsubscribe(self)
        super().dispose()


class _MappedPipe(PipedObservable):
    def __init__(self, source_observable, map_function):
        super().__init__(source_observable)

        self.map_function = map_function
        source_observable.subscribe(self)

    def on_next(self, data):
        mapped_data = self.map_function(data)
        self._push(mapped_data)

    def on_close(self):
        self._close()


class _TimeBufferedPipe(PipedObservable):
    def __init__(self, source_observable: ObservableBase, period_millis, aggregate_function=None):
        super().__init__(source_observable)

        self.period_millis = period_millis
        self.buffer_chunks = []
        self.aggregate_function = aggregate_function
        self.buffer_lock = threading.RLock()
        self.subscriber_lock = threading.RLock()
        self.source_closed = False

        self.flushing_thread = threading.Thread(target=self.flush_buffer)
        self.flushing_thread.start()

        source_observable.subscribe(self)

    def on_next(self, data):
        with self.buffer_lock:
            self.buffer_chunks.append(data)

    def on_close(self):
        self.source_closed = True

    def subscribe(self, observer):
        with self.subscriber_lock:
            super().subscribe(observer)

    def flush_buffer(self):
        while not self.closed:
            source_was_closed = self.source_closed

            current_chunks = None
            with self.buffer_lock:
                if self.buffer_chunks:
                    current_chunks = self.buffer_chunks
                    self.buffer_chunks = []

            with self.subscriber_lock:
                if current_chunks:
                    if self.aggregate_function is not None:
                        current_chunks = self.aggregate_function(current_chunks)

                    for chunk in current_chunks:
                        self._push(chunk)

                if source_was_closed:
                    self._close()
                    return

            time.sleep(self.period_millis / 1000.)


class _StoringObserver:
    def __init__(self):
        self.data = []
        self.closed = False

    def on_next(self, chunk):
        if not self.closed:
            self.data.append(chunk)

    def on_close(self):
        if self.closed:
            raise Exception('Already closed')

        self.closed = True


def read_until_closed(observable, timeout=None):
    """
    Reads and returns all available data in observable until it's closed
    :param observable: data to be read from
    :param timeout: (in sec, float) if timeout is set (non None and > 0) and wait takes more time, 
    then TimeoutError is raised
    :return: all data (list), which will be read 
    """
    observer = _StoringObserver()

    observable.subscribe(observer)
    observable.wait_close(timeout)

    if (timeout is not None) and (not observable.closed):
        observable.unsubscribe(observer)
        raise TimeoutError('Observable was not closed within timeout period of ' + str(timeout) + ' sec')

    return observer.data


class _CloseSubscriber:
    def __init__(self, callback, *args) -> None:
        self._callback = callback
        self._args = args

    def on_next(self, data):
        pass

    def on_close(self):
        self._callback(*self._args)
