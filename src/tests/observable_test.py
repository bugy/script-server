import threading
import time
import unittest

from react.observable import Observable, _StoringObserver, ReplayObservable, PipedObservable, \
    read_until_closed


class TestObservable(unittest.TestCase):
    def _test_no_updates(self, observable):
        observer = _StoringObserver()
        observable.subscribe(observer)

        self.assertEqual([], observer.data)

    def test_no_updates(self):
        observable = self.create_observable()

        self._test_no_updates(observable)

    def _test_single_update(self, source, observable):
        observer = _StoringObserver()
        observable.subscribe(observer)

        message = 'test notification'
        source.push(message)

        return observer, message

    def test_single_update(self):
        observable = self.create_observable()

        observer, message = self._test_single_update(observable, observable)
        self.assertEqual([message], observer.data)

    def test_map_single_update(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer, message = self._test_single_update(observable, mapped_observable)
        self.assertEqual([message + '_x'], observer.data)

    def test_time_buffer_single_update(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        observer, message = self._test_single_update(observable, buffered_observable)
        self.wait_buffer_flush(buffered_observable)

        self.assertEqual([message], observer.data)

    def test_slow_time_buffer_single_update(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(300)

        observer, message = self._test_single_update(observable, buffered_observable)

        self.assertEqual([], observer.data)

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual([message], observer.data)

    def test_time_buffer_aggregate_single_update(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer, message = self._test_single_update(observable, buffered_observable)
        self.wait_buffer_flush(buffered_observable)

        self.assertEqual([message], observer.data)

    def _test_multiple_updates(self, source, observable):
        observer = _StoringObserver()
        observable.subscribe(observer)

        messages = ['m1', '', 'message 3']
        for message in messages:
            source.push(message)

        return observer, messages

    def test_multiple_updates(self):
        observable = self.create_observable()

        observer, messages = self._test_multiple_updates(observable, observable)

        self.assertEqual(messages, observer.data)

    def test_map_multiple_updates(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer, messages = self._test_multiple_updates(observable, mapped_observable)
        messages = [m + '_x' for m in messages]

        self.assertEqual(messages, observer.data)

    def test_time_buffer_multiple_updates(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        observer, messages = self._test_multiple_updates(observable, buffered_observable)
        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(messages, observer.data)

    def test_time_buffer_aggregate_multiple_updates(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer, messages = self._test_multiple_updates(observable, buffered_observable)
        self.wait_buffer_flush(buffered_observable)
        aggregated_message = '|||'.join(messages)

        self.assertEqual([aggregated_message], observer.data)

    def _test_multiple_observers_single_update(self, source, observable):
        observer1 = _StoringObserver()
        observable.subscribe(observer1)

        observer2 = _StoringObserver()
        observable.subscribe(observer2)

        observer3 = _StoringObserver()
        observable.subscribe(observer3)

        message = 'message'
        source.push(message)

        return [observer1, observer2, observer3], message

    def test_multiple_observers_single_update(self):
        observable = self.create_observable()

        observers, message = self._test_multiple_observers_single_update(observable, observable)

        for observer in observers:
            self.assertEqual([message], observer.data)

    def test_map_multiple_observers_single_update(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda x: '_' + x + '_')

        observers, message = self._test_multiple_observers_single_update(observable, mapped_observable)

        for observer in observers:
            self.assertEqual(['_' + message + '_'], observer.data)

    def _test_multiple_observers_multiple_updates(self, source, observable):
        observer1 = _StoringObserver()
        observable.subscribe(observer1)

        observer2 = _StoringObserver()
        observable.subscribe(observer2)

        observer3 = _StoringObserver()
        observable.subscribe(observer3)

        messages = ['message', 'and another one', 'and the third']
        for message in messages:
            source.push(message)

        return [observer1, observer2, observer3], messages

    def test_multiple_observers_multiple_updates(self):
        observable = self.create_observable()

        observers, messages = self._test_multiple_observers_multiple_updates(observable, observable)
        for observer in observers:
            self.assertEqual(messages, observer.data)

    def test_time_buffer_aggregate_multiple_observers_multiple_updates(self):
        observable = self.create_observable()
        time_buffered = observable.time_buffered(100, lambda chunks: ['replacement'])

        observers, messages = self._test_multiple_observers_multiple_updates(observable, time_buffered)
        self.wait_buffer_flush(time_buffered)

        for observer in observers:
            self.assertEqual(['replacement'], observer.data)

    def _test_push_before_late_subscription(self, source, observable, push_postprocessor=None):
        message = 'test1'
        source.push(message)

        if push_postprocessor is not None:
            push_postprocessor()

        observer = _StoringObserver()
        observable.subscribe(observer)

        return observer, message

    def test_push_before_late_subscription(self):
        observable = self.create_observable()

        observer, _ = self._test_push_before_late_subscription(observable, observable)

        self.assertEqual([], observer.data)

    def test_time_buffer_push_before_late_subscription(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        observer, _ = self._test_push_before_late_subscription(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))

        self.assertEqual([], observer.data)

    def test_replay_push_before_late_subscription(self):
        observable = self.create_replay_observable()

        observer, message = self._test_push_before_late_subscription(observable, observable)
        self.assertEqual([message], observer.data)

    def test_pipe_replay_push_before_late_subscription(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        observer, message = self._test_push_before_late_subscription(observable, replay)
        self.assertEqual([message], observer.data)

    def _test_push_after_late_subscription(self, source, observable, push_postprocessor=None):
        early_message = 'test1'
        source.push(early_message)

        if push_postprocessor is not None:
            push_postprocessor()

        observer = _StoringObserver()
        observable.subscribe(observer)

        late_message = 'test3'
        source.push(late_message)

        if push_postprocessor is not None:
            push_postprocessor()

        return observer, early_message, late_message

    def test_push_after_late_subscription(self):
        observable = self.create_observable()

        observer, _, late_message = self._test_push_after_late_subscription(observable, observable)
        self.assertEqual([late_message], observer.data)

    def test_time_buffer_aggregated_push_after_late_subscription(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(100, lambda chunks: ['|'.join(chunks)])

        observer, early_message, late_message = self._test_push_after_late_subscription(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))

        self.assertEqual([late_message], observer.data)

    def test_replay_push_after_late_subscription(self):
        observable = self.create_replay_observable()

        observer, early_message, late_message = self._test_push_after_late_subscription(observable, observable)
        self.assertEqual([early_message, late_message], observer.data)

    def test_pipe_replay_push_after_late_subscription(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        observer, early_message, late_message = self._test_push_after_late_subscription(observable, replay)
        self.assertEqual([early_message, late_message], observer.data)

    def test_replay_time_buffer_aggregated_push_after_late_subscription(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(100, lambda chunks: ['___'.join(chunks)])
        replay = self.replay(buffered_observable)

        observer, early_message, late_message = self._test_push_after_late_subscription(
            observable,
            replay)

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual([early_message + '___' + late_message], observer.data)

    def _test_multiple_updates_before_late_subscription(self, source, observable):
        messages = ['a', 'b', 'c']

        for message in messages:
            source.push(message)

        observer = _StoringObserver()
        observable.subscribe(observer)

        return observer, messages

    def test_multiple_updates_late_subscription(self):
        observable = self.create_observable()

        observer, _ = self._test_multiple_updates_before_late_subscription(observable, observable)
        self.assertEqual([], observer.data)

    def test_map_multiple_updates_late_subscription(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda x: x + '_suffix')

        observer, _ = self._test_multiple_updates_before_late_subscription(observable, mapped_observable)
        self.assertEqual([], observer.data)

    def test_replay_multiple_updates_late_subscription(self):
        observable = self.create_replay_observable()

        observer, messages = self._test_multiple_updates_before_late_subscription(observable, observable)
        self.assertEqual(messages, observer.data)

    def test_pipe_replay_multiple_updates_late_subscription(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        observer, messages = self._test_multiple_updates_before_late_subscription(observable, replay)
        self.assertEqual(messages, observer.data)

    def test_pipe_replay_map_multiple_updates_late_subscription(self):
        observable = self.create_observable()
        replay = self.replay(observable.map(lambda x: x + '_suffix'))

        observer, messages = self._test_multiple_updates_before_late_subscription(observable, replay)
        messages = [x + '_suffix' for x in messages]
        self.assertEqual(messages, observer.data)

    def _test_close(self, source, observable, postclose_callback=None):
        observer = _StoringObserver()
        observable.subscribe(observer)

        source.close()

        if postclose_callback:
            postclose_callback()

        self.assertTrue(observer.closed)
        self.assertTrue(observable.closed)

    def test_close(self):
        observable = self.create_observable()

        self._test_close(observable, observable)

    def test_map_close(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        self._test_close(observable, mapped_observable)

    def test_time_buffer_close(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        self._test_close(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))

    def test_replay_close(self):
        observable = self.create_replay_observable()

        self._test_close(observable, observable)

    def test_pipe_replay_close(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        self._test_close(observable, replay)

    def _test_close_only_subscription_with_callback_arguments(self, source, observable, postclose_callback=None):
        actual_callback_arguments = []

        def callback(value1, value2):
            actual_callback_arguments.append(value1)
            actual_callback_arguments.append(value2)

        observable.subscribe_on_close(callback, 'x', 115)

        source.close()

        if postclose_callback:
            postclose_callback()

        self.assertEqual(['x', 115], actual_callback_arguments)

    def test_close_only_subscription(self):
        observable = self.create_observable()
        self._test_close_only_subscription_with_callback_arguments(observable, observable)

    def test_map_close_only_subscription(self):
        observable = self.create_replay_observable()
        mapped_pipe = observable.map(lambda x: x + '_x')
        self._test_close_only_subscription_with_callback_arguments(observable, mapped_pipe)

    def test_replay_close_only_subscription(self):
        observable = self.create_replay_observable()
        self._test_close_only_subscription_with_callback_arguments(observable, observable)

    def test_close_only_subscription_ignores_on_next(self):
        observable = self.create_observable()

        def callback():
            pass

        observable.subscribe_on_close(callback)

        observable.push('some message')
        observable.close()

    def test_close_multiple_subscribers(self):
        observable = self.create_observable()

        observable.push('test')

        observer1 = _StoringObserver()
        observable.subscribe(observer1)

        observer2 = _StoringObserver()
        observable.subscribe(observer2)

        observable.close()

        self.assertTrue(observer1.closed)
        self.assertTrue(observer2.closed)

    def _test_close_late_subscription(self, source, observable, postclose_callback=None):
        source.push('test')
        source.close()

        if postclose_callback:
            postclose_callback()

        observer = _StoringObserver()
        observable.subscribe(observer)

        self.assertTrue(observer.closed)
        self.assertTrue(observable.closed)

    def test_close_late_subscription(self):
        observable = self.create_observable()

        self._test_close_late_subscription(observable, observable)

    def test_map_close_late_subscription(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        self._test_close_late_subscription(observable, mapped_observable)

    def test_time_buffer_close_late_subscription(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        self._test_close_late_subscription(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))

    def test_replay_close_late_subscription(self):
        observable = self.create_replay_observable()

        self._test_close_late_subscription(observable, observable)

    def test_close_multiple_subscribers_late_subscription(self):
        observable = self.create_observable()

        observable.push('test')
        observable.close()

        observer1 = _StoringObserver()
        observable.subscribe(observer1)

        observer2 = _StoringObserver()
        observable.subscribe(observer2)
        self.assertTrue(observer1.closed)
        self.assertTrue(observer2.closed)

    def _test_wait_close(self, source, observable, postclose_callback=None):
        thread = threading.Thread(target=self.close_delayed, args=[source], daemon=True)
        thread.start()

        observable.wait_close(timeout=0.2)

        if postclose_callback is not None:
            postclose_callback()

        self.assertTrue(observable.closed)

    def test_wait_close(self):
        observable = self.create_observable()

        self._test_wait_close(observable, observable)

    def test_map_wait_close(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        self._test_wait_close(observable, mapped_observable)

    def test_time_buffer_wait_close(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        self._test_wait_close(observable, buffered_observable, buffered_observable.wait_close)

    def test_replay_wait_close(self):
        observable = self.create_replay_observable()

        self._test_wait_close(observable, observable)

    def test_replay_pipe_wait_close(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        self._test_wait_close(observable, replay)

    def test_on_next_exception_once(self):
        observable = self.create_observable()

        class FailingObserver(_StoringObserver):
            def __init__(self):
                super().__init__()
                self.count = 0

            def on_next(self, chunk):
                self.count += 1
                if self.count == 1:
                    raise Exception

                super().on_next(chunk)

        observer = FailingObserver()
        observable.subscribe(observer)

        observable.push('m1')
        observable.push('m2')

        self.assertEqual(['m2'], observer.data)

    def test_on_next_exception_close_afterwards(self):
        observable = self.create_observable()

        class FailingObserver(_StoringObserver):
            def on_next(self, chunk):
                raise Exception

        observer = FailingObserver()
        observable.subscribe(observer)

        observable.push('m1')
        observable.push('m2')
        observable.close()

        self.assertEqual([], observer.data)
        self.assertTrue(observer.closed)

    def test_on_next_exception_different_observers(self):
        observable = self.create_observable()

        class FailingObserver(_StoringObserver):
            def on_next(self, chunk):
                raise Exception

        failing_observer = FailingObserver()
        observable.subscribe(failing_observer)

        normal_observer = _StoringObserver()
        observable.subscribe(normal_observer)

        observable.push('m1')
        observable.push('m2')

        self.assertEqual([], failing_observer.data)
        self.assertEqual(['m1', 'm2'], normal_observer.data)

    def test_on_close_exception_single_observer(self):
        observable = self.create_observable()

        class FailingObserver(_StoringObserver):
            def on_close(self):
                raise Exception

        observer = FailingObserver()
        observable.subscribe(observer)

        observable.close()

        self.assertTrue(observable.closed)

    def test_on_close_exception_different_observers(self):
        observable = self.create_observable()

        class FailingObserver(_StoringObserver):
            def on_close(self):
                raise Exception

        failing_observer = FailingObserver()
        observable.subscribe(failing_observer)

        normal_observer = _StoringObserver()
        observable.subscribe(normal_observer)

        observable.close()

        self.assertTrue(observable.closed)
        self.assertTrue(normal_observer.closed)

    def test_prohibit_piped_modifications(self):
        pipe_creators = [
            lambda o: o.map(lambda x: '_' + x),
            lambda o: o.time_buffered(10),
            lambda o: self.replay(o)
        ]

        for pipe_creator in pipe_creators:
            observable = self.create_observable()
            pipe = pipe_creator(observable)

            self.assertRaises(RuntimeError, pipe.push, ['any_message'])
            self.assertRaises(RuntimeError, pipe.close)

    def test_time_buffer_multiple_buffers(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observer = _StoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('message1')

        self.wait_buffer_flush(buffered_observable)

        observable.push('message2')

        self.wait_buffer_flush(buffered_observable)

        observable.push('message3')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['message1', 'message2', 'message3'], observer.data)

    def test_time_buffer_aggregate_multiple_updates_multiple_buffers(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer = _StoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('a')
        observable.push('b')
        observable.push('c')

        self.wait_buffer_flush(buffered_observable)

        observable.push('d')
        observable.push('e')
        observable.push('f')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['a|||b|||c', 'd|||e|||f'], observer.data)

    def test_time_buffer_flush_before_close(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100)

        observer = _StoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('m1')
        observable.push('m2')
        observable.close()

        self.assertEqual([], observer.data)
        self.assertFalse(observer.closed)

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['m1', 'm2'], observer.data)
        self.assertTrue(observer.closed)

    def _test_read_until_closed(self, source, observable, prewait_callback=None):
        early_messages = ['early 1', 'early 1']
        late_messages = ['lateX', 'lateY']

        for message in early_messages:
            source.push(message)

        def publish_async():
            time.sleep(0.1)

            for message in late_messages:
                source.push(message)

            source.close()

        thread = threading.Thread(target=publish_async, daemon=True)
        thread.start()

        if prewait_callback:
            prewait_callback()

        data = read_until_closed(observable, timeout=0.3)

        self.assertTrue(source.closed)
        self.assertTrue(observable.closed)

        return data, early_messages, late_messages

    def test_read_until_closed(self):
        observable = self.create_observable()

        data, _, late_messages = self._test_read_until_closed(observable, observable)

        self.assertEqual(late_messages, data)

    def test_map_read_until_closed(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        data, _, late_messages = self._test_read_until_closed(observable, mapped_observable)
        late_messages = [m + '_x' for m in late_messages]

        self.assertEqual(late_messages, data)

    def test_time_buffer_read_until_closed(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        data, _, late_messages = self._test_read_until_closed(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))

        self.assertEqual(late_messages, data)

    def test_time_buffer_aggregated_read_until_closed(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(100, lambda chunks: ['|'.join(chunks)])

        data, _, late_messages = self._test_read_until_closed(
            observable,
            buffered_observable,
            lambda: self.wait_buffer_flush(buffered_observable))
        message = '|'.join(late_messages)

        self.assertEqual([message], data)

    def test_time_buffer_not_flushed_read_until_closed(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(300)

        observable.push('m1')
        observable.push('m2')
        observable.close()

        self.assertFalse(buffered_observable.closed)
        self.assertTrue(observable.closed)

        self.assertRaises(TimeoutError, read_until_closed, buffered_observable, 0.001)

    def test_replay_read_until_closed(self):
        observable = self.create_replay_observable()

        data, early_messages, late_messages = self._test_read_until_closed(observable, observable)

        self.assertEqual(early_messages + late_messages, data)

    def test_pipe_replay_read_until_closed(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        data, early_messages, late_messages = self._test_read_until_closed(observable, replay)

        self.assertEqual(early_messages + late_messages, data)

    def test_replay_dispose(self):
        observable = self.create_replay_observable()
        observable.push('1')
        observable.close()
        observable.dispose()

        data = read_until_closed(observable, 0.1)
        self.assertEqual([], data)

    def test_replay_dispose_when_active(self):
        observable = self.create_replay_observable()
        observable.push('1')
        observable.dispose()

        self.assertTrue(observable.closed)
        self.assertEqual([], read_until_closed(observable, timeout=0.001))

    def test_pipe_replay_dispose_deferred(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        observer = _StoringObserver()
        replay.subscribe(observer)

        replay.dispose()

        self.assertFalse(replay.closed)
        self.assertFalse(observer.closed)

        observable.close()
        self.assertTrue(replay.closed)
        self.assertTrue(observer.closed)

    def test_pipe_replay_dispose_deferred_for_updates(self):
        observable = self.create_observable()
        replay = self.replay(observable)

        observer = _StoringObserver()
        replay.subscribe(observer)

        observable.push('1')
        replay.dispose()
        observable.push('2')

        self.assertEqual(['1', '2'], observer.data)

        observable.close()
        self.assertEqual([], read_until_closed(replay, timeout=0.001))

    def test_unlimited_wait_close(self):
        observable = self.create_observable()

        thread = threading.Thread(target=observable.wait_close, daemon=True)
        thread.start()

        time.sleep(0.1)

        self.assertTrue(thread.is_alive())
        observable.close()

        thread.join(timeout=0.1)
        self.assertFalse(thread.is_alive())

    def create_observable(self):
        observable = Observable()
        self._track(observable)
        return observable

    def replay(self, observable):
        replay = observable.replay()
        self._track(observable)
        return replay

    def create_replay_observable(self):
        observable = ReplayObservable()
        self._track(observable)
        return observable

    def _track(self, observable):
        self._observables.append(observable)

    def setUp(self):
        super().setUp()
        self._observables = []

    def tearDown(self):
        super().tearDown()

        for observable in self._observables:
            if not observable.closed and not isinstance(observable, PipedObservable):
                observable.close()

            if isinstance(observable, ReplayObservable):
                observable.dispose()

    @staticmethod
    def close_delayed(observable):
        time.sleep(0.1)
        observable.close()

    @staticmethod
    def wait_buffer_flush(buffered_observable):
        time.sleep(buffered_observable.period_millis * 1.3 / 1000.0 + 0.01)
