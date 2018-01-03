import abc
import logging
import threading
import time
from typing import List, TypeVar, Generic

T = TypeVar('T')

LOGGER = logging.getLogger('script_server.observable')


class ObservableBase(Generic[T], metaclass=abc.ABCMeta):
    def __init__(self):
        self.observers = []
        self.closed = False
        self.chunks = []
        self.close_condition = threading.Condition()

    def push(self, data: T):
        self._push(data)

    def _push(self, data: T):
        self.chunks.append(data)

        self._fire_on_next(data)

    def close(self):
        self._close()

    def _close(self):
        with self.close_condition:
            self.closed = True
            self.close_condition.notify_all()

        self._fire_on_close()

    def subscribe(self, observer):
        for chunk in self.chunks:
            observer.on_next(chunk)

        if self.closed:
            observer.on_close()
            return

        self.observers.append(observer)

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

    def get_old_data(self) -> List[T]:
        return self.chunks

    def time_buffered(self, period_millis, aggregate_function=None):
        return _TimeBufferedPipe(self, period_millis, aggregate_function)

    def map(self, map_function):
        return _MappedPipe(self, map_function)

    def wait_close(self):
        with self.close_condition:
            while not self.closed:
                self.close_condition.wait()


class Observable(ObservableBase[T]):
    def __init__(self):
        super().__init__()


class _PipedObservable(ObservableBase[T]):
    def __init__(self, source_observable):
        super().__init__()

        self.origin = source_observable

    def push(self, data):
        raise RuntimeError('Piped observable is read-only')

    def close(self):
        raise RuntimeError('Piped observable is read-only')


class _MappedPipe(_PipedObservable):
    def __init__(self, source_observable, map_function):
        super().__init__(source_observable)

        self.map_function = map_function
        source_observable.subscribe(self)

    def on_next(self, data):
        mapped_data = self.map_function(data)
        self._push(mapped_data)

    def on_close(self):
        self._close()


class _TimeBufferedPipe(_PipedObservable):
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
            for chunk in self.chunks:
                observer.on_next(chunk)

            if self.closed:
                observer.on_close()
                return

            self.observers.append(observer)

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
