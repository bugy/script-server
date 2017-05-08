import os
import unittest

import model_helper
import script_configs


class TestDefaultValue(unittest.TestCase):
    env_key = 'test_val'

    def test_no_value(self):
        parameter = script_configs.Parameter()

        default = model_helper.get_default(parameter)
        self.assertEqual(default, None)

    def test_empty_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, '')

    def test_text_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default('text')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_unicode_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(u'text')

        default = model_helper.get_default(parameter)
        self.assertEqual(default, u'text')

    def test_int_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(5)

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 5)

    def test_bool_value(self):
        parameter = script_configs.Parameter()
        parameter.set_default(True)

        default = model_helper.get_default(parameter)
        self.assertEqual(default, True)

    def test_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        os.environ[self.env_key] = 'text'

        default = model_helper.get_default(parameter)
        self.assertEqual(default, 'text')

    def test_missing_env_variable(self):
        parameter = script_configs.Parameter()
        parameter.set_default('$$test_val')

        self.assertRaises(Exception, model_helper.get_default, parameter)

    def tearDown(self):
        if self.env_key in os.environ:
            del os.environ[self.env_key]


if __name__ == '__main__':
    unittest.main()
