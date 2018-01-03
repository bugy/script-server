import threading
import time
import unittest

from react.observable import Observable
from tests.test_utils import SimpleStoringObserver


class TestObservable(unittest.TestCase):
    def test_no_updates(self):
        observable = self.create_observable()
        observable.close()

        self.assertEqual([], observable.get_old_data())

    def test_single_update(self):
        observable = self.create_observable()

        observer = SimpleStoringObserver()
        observable.subscribe(observer)

        observable.push('test')

        self.assertEqual(['test'], observer.data)

    def test_multiple_updates(self):
        observable = self.create_observable()

        observer = SimpleStoringObserver()
        observable.subscribe(observer)

        observable.push('1')
        observable.push('2')
        observable.push('3')

        self.assertEqual(['1', '2', '3'], observer.data)

    def test_multiple_observers_single_update(self):
        observable = self.create_observable()

        observer1 = SimpleStoringObserver()
        observable.subscribe(observer1)

        observer2 = SimpleStoringObserver()
        observable.subscribe(observer2)

        observer3 = SimpleStoringObserver()
        observable.subscribe(observer3)

        observable.push('message')

        self.assertEqual(['message'], observer1.data)
        self.assertEqual(['message'], observer2.data)
        self.assertEqual(['message'], observer3.data)

    def test_multiple_observers_multiple_updates(self):
        observable = self.create_observable()

        observer1 = SimpleStoringObserver()
        observable.subscribe(observer1)

        observer2 = SimpleStoringObserver()
        observable.subscribe(observer2)

        observer3 = SimpleStoringObserver()
        observable.subscribe(observer3)

        observable.push('message')
        observable.push('and another one')
        observable.push('and the third')

        self.assertEqual(['message', 'and another one', 'and the third'], observer1.data)
        self.assertEqual(['message', 'and another one', 'and the third'], observer2.data)
        self.assertEqual(['message', 'and another one', 'and the third'], observer3.data)

    def test_single_update_late_subscription(self):
        observable = self.create_observable()

        observable.push('test')

        observer = SimpleStoringObserver()
        observable.subscribe(observer)

        self.assertEqual(['test'], observer.data)

    def test_multiple_updates_late_subscription(self):
        observable = self.create_observable()

        observable.push('test1')
        observable.push('test2')
        observable.push('test3')

        observer = SimpleStoringObserver()
        observable.subscribe(observer)

        self.assertEqual(['test1', 'test2', 'test3'], observer.data)

    def test_close(self):
        observable = self.create_observable()

        observable.push('test')

        observer = SimpleStoringObserver()
        observable.subscribe(observer)

        observable.close()

        self.assertTrue(observer.closed)

    def test_close_multiple_subscribers(self):
        observable = self.create_observable()

        observable.push('test')

        observer1 = SimpleStoringObserver()
        observable.subscribe(observer1)

        observer2 = SimpleStoringObserver()
        observable.subscribe(observer2)

        observable.close()

        self.assertTrue(observer1.closed)
        self.assertTrue(observer2.closed)

    def test_close_late_subscription(self):
        observable = self.create_observable()

        observable.push('test')
        observable.close()

        observer = SimpleStoringObserver()
        observable.subscribe(observer)
        self.assertTrue(observer.closed)

    def test_close_multiple_subscribers_late_subscription(self):
        observable = self.create_observable()

        observable.push('test')
        observable.close()

        observer1 = SimpleStoringObserver()
        observable.subscribe(observer1)

        observer2 = SimpleStoringObserver()
        observable.subscribe(observer2)
        self.assertTrue(observer1.closed)
        self.assertTrue(observer2.closed)

    def test_wait_close(self):
        observable = self.create_observable()

        thread = threading.Thread(target=self.close_delayed, args=[observable], daemon=True)
        thread.start()

        observable.wait_close()

        self.assertTrue(observable.closed)

    def test_get_old_data(self):
        observable = self.create_observable()

        observable.push('m1')
        observable.push('m2')

        self.assertEqual(['m1', 'm2'], observable.get_old_data())

    def test_on_next_exception_once(self):
        observable = self.create_observable()

        class FailingObserver(SimpleStoringObserver):
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

        class FailingObserver(SimpleStoringObserver):
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

        class FailingObserver(SimpleStoringObserver):
            def on_next(self, chunk):
                raise Exception

        failing_observer = FailingObserver()
        observable.subscribe(failing_observer)

        normal_observer = SimpleStoringObserver()
        observable.subscribe(normal_observer)

        observable.push('m1')
        observable.push('m2')

        self.assertEqual([], failing_observer.data)
        self.assertEqual(['m1', 'm2'], normal_observer.data)

    def test_on_close_exception_single_observer(self):
        observable = self.create_observable()

        class FailingObserver(SimpleStoringObserver):
            def on_close(self):
                raise Exception

        observer = FailingObserver()
        observable.subscribe(observer)

        observable.close()

        self.assertTrue(observable.closed)

    def test_on_close_exception_different_observers(self):
        observable = self.create_observable()

        class FailingObserver(SimpleStoringObserver):
            def on_close(self):
                raise Exception

        failing_observer = FailingObserver()
        observable.subscribe(failing_observer)

        normal_observer = SimpleStoringObserver()
        observable.subscribe(normal_observer)

        observable.close()

        self.assertTrue(observable.closed)
        self.assertTrue(normal_observer.closed)

    def test_map_single_update(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        observable.push('message')

        self.assertEqual(['message_x'], observer.data)

    def test_map_multiple_updates(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        observable.push('message1')
        observable.push('')
        observable.push('message2')

        self.assertEqual(['message1_x', '_x', 'message2_x'], observer.data)

    def test_map_multiple_updates_late_subscription(self):
        observable = self.create_observable()

        observable.push('a')
        observable.push('b')
        observable.push('c')

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        self.assertEqual(['a_x', 'b_x', 'c_x'], observer.data)

    def test_map_get_old_data(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observable.push('message1')
        observable.push('message2')

        self.assertEqual(['message1_x', 'message2_x'], mapped_observable.get_old_data())

    def test_map_close(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        observable.close()

        self.assertTrue(observer.closed)
        self.assertTrue(mapped_observable.closed)

    def test_map_close_late_subscription(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observable.close()

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        self.assertTrue(observer.closed)

    def test_map_wait_close(self):
        observable = self.create_observable()

        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        observer = SimpleStoringObserver()
        mapped_observable.subscribe(observer)

        thread = threading.Thread(target=self.close_delayed, args=[observable], daemon=True)
        thread.start()

        mapped_observable.wait_close()

        self.assertTrue(observer.closed)

    def test_map_prohibit_push(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        self.assertRaises(RuntimeError, mapped_observable.push, ['any_message'])

    def test_map_prohibit_close(self):
        observable = self.create_observable()
        mapped_observable = observable.map(lambda chunk: chunk + '_x')

        self.assertRaises(RuntimeError, mapped_observable.close)

    def test_time_buffer_single_update(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('message1')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['message1'], observer.data)

    def test_time_buffer_multiple_updates(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('a')
        observable.push('b')
        observable.push('c')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['a', 'b', 'c'], observer.data)

    def test_time_buffer_multiple_buffers(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('message1')

        self.wait_buffer_flush(buffered_observable)

        observable.push('message2')

        self.wait_buffer_flush(buffered_observable)

        observable.push('message3')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['message1', 'message2', 'message3'], observer.data)

    def test_time_buffer_not_flushed(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(300)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('message1')

        self.assertEqual([], observer.data)

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['message1'], observer.data)

    def test_time_buffer_aggregate_single_update(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('message1')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['message1'], observer.data)

    def test_time_buffer_aggregate_multiple_updates(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('a')
        observable.push('b')
        observable.push('c')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['a|||b|||c'], observer.data)

    def test_time_buffer_aggregate_multiple_updates_multiple_buffers(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|||'.join(chunks)])

        observer = SimpleStoringObserver()
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

    def test_time_buffer_close(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.close()

        self.wait_buffer_flush(buffered_observable)

        self.assertTrue(observer.closed)
        self.assertTrue(buffered_observable.closed)

    def test_time_buffer_flush_before_close(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        observable.push('m1')
        observable.push('m2')
        observable.close()

        self.assertEqual([], observer.data)
        self.assertFalse(observer.closed)

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['m1', 'm2'], observer.data)
        self.assertTrue(observer.closed)

    def test_time_buffer_prohibit_push(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        self.assertRaises(RuntimeError, buffered_observable.push, ['any_message'])

    def test_time_buffer_prohibit_close(self):
        observable = self.create_observable()
        buffered_observable = observable.time_buffered(10)

        self.assertRaises(RuntimeError, buffered_observable.close)

    def test_time_buffer_get_old_data(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observable.push('m1')
        observable.push('m2')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['m1', 'm2'], buffered_observable.get_old_data())

    def test_time_buffer_get_old_data_not_flushed(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(300)

        observable.push('m1')
        observable.push('m2')

        self.assertEqual([], buffered_observable.get_old_data())

    def test_time_buffer_get_old_data_aggregated(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|'.join(chunks)])

        observable.push('a')
        observable.push('b')
        observable.push('c')

        self.wait_buffer_flush(buffered_observable)

        self.assertEqual(['a|b|c'], buffered_observable.get_old_data())

    def test_time_buffer_wait_close(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        self.close_delayed(observable)

        buffered_observable.wait_close()

        self.assertTrue(buffered_observable.closed)

    def test_time_buffer_late_subscription(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observable.push('m1')
        observable.push('m2')

        self.wait_buffer_flush(buffered_observable)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        self.assertEqual(['m1', 'm2'], observer.data)

    def test_time_buffer_aggregated_late_subscription(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(100, lambda chunks: ['|'.join(chunks)])

        observable.push('m1')
        observable.push('m2')
        observable.push('m3')

        self.wait_buffer_flush(buffered_observable)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        self.assertEqual(['m1|m2|m3'], observer.data)

    def test_time_buffer_close_late_subscription(self):
        observable = self.create_observable()

        buffered_observable = observable.time_buffered(10)

        observable.push('message')
        observable.close()

        self.wait_buffer_flush(buffered_observable)

        observer = SimpleStoringObserver()
        buffered_observable.subscribe(observer)

        self.assertTrue(observer.closed)

    def create_observable(self):
        self.observable = Observable()
        return self.observable

    def tearDown(self):
        super().tearDown()

        if not self.observable.closed:
            self.observable.close()

    @staticmethod
    def close_delayed(observable):
        time.sleep(0.1)
        observable.close()

    @staticmethod
    def wait_buffer_flush(buffered_observable):
        time.sleep(buffered_observable.period_millis * 1.3 / 1000.0 + 0.01)
