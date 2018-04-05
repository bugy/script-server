import unittest

from execution.id_generator import IdGenerator
from model.model_helper import is_empty


class TestIdGenerator(unittest.TestCase):
    def test_next_id(self):
        generator = IdGenerator([])
        id = generator.next_id()
        self.assertIsNotNone(id)
        self.assertIsInstance(id, str)
        self.assertFalse(is_empty(id))

    def test_2_next_ids(self):
        generator = IdGenerator([])
        id1 = generator.next_id()
        id2 = generator.next_id()
        self.assertNotEqual(id1, id2)

    def test_3_next_ids(self):
        generator = IdGenerator([])
        id1 = generator.next_id()
        id2 = generator.next_id()
        id3 = generator.next_id()
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id1, id3)
        self.assertNotEqual(id2, id3)

    def test_unique_id_after_init(self):
        generator1 = IdGenerator([])
        ids = []
        for index in range(10):
            ids.append(generator1.next_id())

        generator2 = IdGenerator(ids)
        next_id = generator2.next_id()
        self.assertFalse(next_id in ids)

    def test_unique_id_after_init_with_random_ids(self):
        ids = ['test1', '123', '1', '3', '10', 'my_script#5']
        generator = IdGenerator(ids)

        for index in range(50):
            next_id = generator.next_id()
            self.assertFalse(next_id in ids)
            ids.append(next_id)
