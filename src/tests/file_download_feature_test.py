import os
import unittest

from features import file_download_feature
from tests import test_utils
from tests.test_utils import create_parameter_model
from utils import file_utils


class TestFileMatching(unittest.TestCase):
    def test_simple_match(self):
        files = file_download_feature.find_matching_files('/home/user/test.txt', None)

        self.assertEqual(files, ['/home/user/test.txt'])

    def test_single_asterisk_1_match(self):
        test_utils.create_file('test.txt')

        files = file_download_feature.find_matching_files('*/test.txt', None)

        self.assertEqual(files, [os.path.join(test_utils.temp_folder, 'test.txt')])

    def test_single_asterisk_2_matches(self):
        test_utils.create_file('test1.txt')
        test_utils.create_file('test2.txt')

        files = file_download_feature.find_matching_files('*/test*.txt', None)

        self.assertCountEqual(files, [
            os.path.join(test_utils.temp_folder, 'test1.txt'),
            os.path.join(test_utils.temp_folder, 'test2.txt')
        ])

    def test_double_asterisk_match(self):
        test_utils.create_file(os.path.join('test', 'test.txt'))

        files = set(file_download_feature.find_matching_files(test_utils.temp_folder + '/**', None))

        self.assertCountEqual(files, {
            os.path.join(test_utils.temp_folder, ''),
            os.path.join(test_utils.temp_folder, 'test'),
            os.path.join(test_utils.temp_folder, 'test', 'test.txt')
        })

    def test_double_asterisk_match_multiple_files(self):
        test_utils.create_file(os.path.join('f1', 'test1.txt'))
        test_utils.create_file(os.path.join('f1', 'test2.txt'))
        test_utils.create_file(os.path.join('f2', 'test3.txt'))

        files = set(file_download_feature.find_matching_files(test_utils.temp_folder + '/**', None))

        self.assertCountEqual(files, {
            os.path.join(test_utils.temp_folder, ''),
            os.path.join(test_utils.temp_folder, 'f1'),
            os.path.join(test_utils.temp_folder, 'f1', 'test1.txt'),
            os.path.join(test_utils.temp_folder, 'f1', 'test2.txt'),
            os.path.join(test_utils.temp_folder, 'f2'),
            os.path.join(test_utils.temp_folder, 'f2', 'test3.txt')
        })

    def test_double_asterisk_match_multiple_files_when_complex(self):
        test_utils.create_file(os.path.join('f1', 'test1.txt'))
        test_utils.create_file(os.path.join('f1', 'test2.txt'))
        test_utils.create_file(os.path.join('d2', 'test3.txt'))
        test_utils.create_file(os.path.join('d2', 'd3', 'test4.txt'))
        test_utils.create_file(os.path.join('d3', 'd4', 'd5', 'test5.png'))
        test_utils.create_file(os.path.join('d3', 'd6', 'd7', 'test6.txt'))

        temp_folder = file_utils.normalize_path(test_utils.temp_folder)
        files = set(file_download_feature.find_matching_files(temp_folder + '/d*/**/*.txt', None))

        self.assertCountEqual(files, {
            os.path.join(temp_folder, 'd2', 'test3.txt'),
            os.path.join(temp_folder, 'd2', 'd3', 'test4.txt'),
            os.path.join(temp_folder, 'd3', 'd6', 'd7', 'test6.txt')
        })

    def test_regex_only_0_matches(self):
        files = file_download_feature.find_matching_files('#\d+#', 'some text without numbers')

        self.assertEqual(files, [])

    def test_regex_only_1_match(self):
        files = file_download_feature.find_matching_files('#(\/[^\/]+)+#', 'the text is in /home/username/text.txt')

        self.assertEqual(files, ['/home/username/text.txt'])

    def test_regex_only_3_matches(self):
        files = file_download_feature.find_matching_files('#(\/([\w.\-]|(\\\ ))+)+#', 'found files: '
                                                                                      '/home/username/text.txt, '
                                                                                      '/tmp/data.dat, '
                                                                                      '/opt/software/script\ server/read_me.md')

        self.assertEqual(files, ['/home/username/text.txt', '/tmp/data.dat', '/opt/software/script\ server/read_me.md'])

    def test_regex_only_any_path_linux_3_matches(self):
        test_utils.set_linux()

        files = file_download_feature.find_matching_files('##any_path#', 'found files: '
                                                                         '/home/username/text.txt, '
                                                                         '/tmp/data.dat, '
                                                                         '/opt/software/script\ server/read_me.md')

        self.assertEqual(files, ['/home/username/text.txt', '/tmp/data.dat', '/opt/software/script\ server/read_me.md'])

    def test_regex_only_any_path_win_3_matches(self):
        test_utils.set_win()

        files = file_download_feature.find_matching_files('##any_path#', 'found files: '
                                                                         'C:\\Users\\username\\text.txt, '
                                                                         'D:\\windows\\System32, '
                                                                         'C:\\Program\ Files\\script\ server\\read_me.md')

        self.assertEqual(files, ['C:\\Users\\username\\text.txt',
                                 'D:\\windows\\System32',
                                 'C:\\Program\ Files\\script\ server\\read_me.md'])

    def test_regex_only_search_user_home_win(self):
        test_utils.set_win()

        files = file_download_feature.find_matching_files('##any_path#', 'found files: '
                                                                         '~\\text.txt')

        self.assertEqual(files, ['~\\text.txt'])

    def test_1_regex_and_text_no_matches(self):
        files = file_download_feature.find_matching_files('/home/username/#\d+#', 'username=some_name\n '
                                                                                  'folder=some_folder\n '
                                                                                  'time=now')

        self.assertEqual(files, [])

    def test_1_regex_and_text_1_match(self):
        files = file_download_feature.find_matching_files('/home/username/#\d+#', 'username=some_name\n '
                                                                                  'folder=some_folder\n '
                                                                                  'time=153514')

        self.assertEqual(files, ['/home/username/153514'])

    def test_1_regex_and_text_3_matches(self):
        files = file_download_feature.find_matching_files('/home/username/#\d+#', 'username=some_name\n '
                                                                                  'folder=some_folder\n '
                                                                                  'time=153514\n '
                                                                                  'age=18, size=256Mb')

        self.assertEqual(files, ['/home/username/153514', '/home/username/18', '/home/username/256'])

    def test_1_regex_with_first_group_and_text_1_match(self):
        files = file_download_feature.find_matching_files('/home/#1#username=(\w+)#/file.txt', 'username=some_name\n '
                                                                                               'folder=some_folder\n '
                                                                                               'time=153514\n '
                                                                                               'age=18, size=256Mb')

        self.assertEqual(files, ['/home/some_name/file.txt'])

    def test_1_regex_with_second_group_and_text_2_matches(self):
        files = file_download_feature.find_matching_files('/home/username/#2#=(some_(\w+))#.txt',
                                                          'username=some_name\n '
                                                          'folder=some_folder\n '
                                                          'time=153514\n '
                                                          'age=18, size=256Mb')

        self.assertEqual(files, ['/home/username/name.txt', '/home/username/folder.txt'])

    def test_2_regexes_1_match(self):
        files = file_download_feature.find_matching_files('/home/#2#username=((\w+))#/#1#time=(\d+)#.txt',
                                                          'username=some_name\n '
                                                          'folder=some_folder\n '
                                                          'time=153514\n '
                                                          'age=18, size=256Mb')

        self.assertEqual(files, ['/home/some_name/153514.txt'])

    def test_1_regex_and_asterisk(self):
        test_utils.create_file(os.path.join('some_folder', 'file.txt'))

        files = file_download_feature.find_matching_files('*/#1#folder=(\w+)#/*.txt', 'username=some_name\n '
                                                                                      'folder=some_folder\n '
                                                                                      'time=153514\n '
                                                                                      'age=18, size=256Mb')

        self.assertEqual(files, [os.path.join(test_utils.temp_folder, 'some_folder', 'file.txt')])

    def setUp(self):
        test_utils.setup()

    def tearDown(self):
        test_utils.cleanup()


class TestParametersSubstitute(unittest.TestCase):
    def test_no_parameters(self):
        files = file_download_feature.substitute_parameter_values([], ['/home/user/test.txt'], [])

        self.assertEqual(files, ['/home/user/test.txt'])

    def test_single_replace(self):
        parameter = create_parameter_model('param1')

        files = file_download_feature.substitute_parameter_values(
            [parameter],
            ['/home/user/${param1}.txt'],
            {'param1': 'val1'})

        self.assertEqual(files, ['/home/user/val1.txt'])

    def test_two_replaces(self):
        parameters = []
        parameters.append(create_parameter_model('param1', all_parameters=parameters))
        parameters.append(create_parameter_model('param2', all_parameters=parameters))

        files = file_download_feature.substitute_parameter_values(
            parameters,
            ['/home/${param2}/${param1}.txt'],
            {'param1': 'val1', 'param2': 'val2'})

        self.assertEqual(files, ['/home/val2/val1.txt'])

    def test_two_replaces_in_two_files(self):
        parameters = []
        parameters.append(create_parameter_model('param1', all_parameters=parameters))
        parameters.append(create_parameter_model('param2', all_parameters=parameters))

        files = file_download_feature.substitute_parameter_values(
            parameters,
            ['/home/${param2}/${param1}.txt', '/tmp/${param2}.txt', '/${param1}'],
            {'param1': 'val1', 'param2': 'val2'})

        self.assertEqual(files, ['/home/val2/val1.txt', '/tmp/val2.txt', '/val1'])

    def test_no_pattern_match(self):
        param1 = create_parameter_model('param1')

        files = file_download_feature.substitute_parameter_values(
            [param1],
            ['/home/user/${paramX}.txt'],
            {'param1': 'val1'})

        self.assertEqual(files, ['/home/user/${paramX}.txt'])

    def test_skip_secure_replace(self):
        param1 = create_parameter_model('param1', secure=True)

        files = file_download_feature.substitute_parameter_values(
            [param1],
            ['/home/user/${param1}.txt'],
            {'param1': 'val1'})

        self.assertEqual(files, ['/home/user/${param1}.txt'])

    def test_skip_flag_replace(self):
        param1 = create_parameter_model('param1', no_value=True)

        files = file_download_feature.substitute_parameter_values(
            [param1],
            ['/home/user/${param1}.txt'],
            {'param1': 'val1'})

        self.assertEqual(files, ['/home/user/${param1}.txt'])

