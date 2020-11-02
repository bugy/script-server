from unittest import TestCase

from utils import os_utils, file_utils


class TestToFilename(TestCase):
    def test_replace_special_characters_linux(self):
        os_utils.set_linux()

        filename = file_utils.to_filename('!@#$%^&*()_+\|/?.<>,\'"')
        self.assertEqual('!@#$%^&*()_+\\|_?.<>,\'"', filename)

    def test_replace_special_characters_windows(self):
        os_utils.set_win()

        filename = file_utils.to_filename('!@#$%^&*()_+\|/?.<>,\'"')
        self.assertEqual('!@#$%^&_()_+____.__,\'_', filename)

    def tearDown(self) -> None:
        os_utils.reset_os()
