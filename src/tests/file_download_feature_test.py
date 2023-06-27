import os
import threading
import unittest

from auth.user import User
from execution import executor
from execution.execution_service import ExecutionService
from features import file_download_feature
from features.file_download_feature import FileDownloadFeature
from files.user_file_storage import UserFileStorage
from tests import test_utils
from tests.test_utils import create_parameter_model, _MockProcessWrapper, _IdGeneratorMock, create_config_model, \
    create_audit_names, create_script_param_config, AnyUserAuthorizer, wrap_values
from utils import file_utils, os_utils
from utils.file_utils import normalize_path

DEFAULT_USER = User('userX', {})


class TestFileMatching(unittest.TestCase):
    def test_simple_match(self):
        files = file_download_feature.find_matching_files('/home/user/test.txt', None)

        self.assertEqual(files, ['/home/user/test.txt'])

    def test_single_asterisk_1_match(self):
        test_utils.create_file('test.txt')

        files = file_download_feature.find_matching_files('*/test.txt', None)

        self.assertEqual(files, [os.path.join(test_utils.temp_folder, 'test.txt')])

    def test_single_asterisk_2_matches(self):
        test_utils.create_file('test1.log')
        test_utils.create_file('test2.log')

        files = file_download_feature.find_matching_files('*/test*.log', None)

        self.assertCountEqual(files, [
            os.path.join(test_utils.temp_folder, 'test1.log'),
            os.path.join(test_utils.temp_folder, 'test2.log')
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
        files = file_download_feature.substitute_variable_values(
            [], ['/home/user/test.txt'], [],
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/test.txt'])

    def test_single_replace(self):
        parameter = create_parameter_model('param1')

        parameters = [parameter]
        value_wrappers = wrap_values(parameters, {'param1': 'val1'})
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${param1}.txt'],
            value_wrappers,
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/val1.txt'])

    def test_two_replaces(self):
        parameters = []
        parameters.append(create_parameter_model('param1', all_parameters=parameters))
        parameters.append(create_parameter_model('param2', all_parameters=parameters))

        value_wrappers = wrap_values(parameters, {'param1': 'val1', 'param2': 'val2'})
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/${param2}/${param1}.txt'],
            value_wrappers,
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/val2/val1.txt'])

    def test_two_replaces_in_two_files(self):
        parameters = []
        parameters.append(create_parameter_model('param1', all_parameters=parameters))
        parameters.append(create_parameter_model('param2', all_parameters=parameters))

        value_wrappers = wrap_values(parameters, {'param1': 'val1', 'param2': 'val2'})
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/${param2}/${param1}.txt', '/tmp/${param2}.txt', '/${param1}'],
            value_wrappers,
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/val2/val1.txt', '/tmp/val2.txt', '/val1'])

    def test_no_pattern_match(self):
        param1 = create_parameter_model('param1')

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${paramX}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/${paramX}.txt'])

    def test_skip_secure_replace(self):
        param1 = create_parameter_model('param1', secure=True)

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${param1}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/${param1}.txt'])

    def test_skip_flag_replace(self):
        param1 = create_parameter_model('param1', no_value=True)

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${param1}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/${param1}.txt'])

    def test_replace_audit_name(self):
        param1 = create_parameter_model('param1', no_value=True)

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${auth.audit_name}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/127.0.0.1.txt'])

    def test_replace_username(self):
        param1 = create_parameter_model('param1', no_value=True)

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/user/${auth.username}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user/user_X.txt'])

    def test_replace_username_and_param(self):
        param1 = create_parameter_model('param1')

        parameters = [param1]
        files = file_download_feature.substitute_variable_values(
            parameters,
            ['/home/${auth.username}/${param1}.txt'],
            wrap_values(parameters, {'param1': 'val1'}),
            '127.0.0.1',
            'user_X')

        self.assertEqual(files, ['/home/user_X/val1.txt'])


class FileDownloadFeatureTest(unittest.TestCase):

    def test_prepare_file_on_finish(self):
        file1_path = test_utils.create_file('file1.txt')

        downloadable_files = self.perform_execution([file1_path])

        self.assert_downloadable_files(downloadable_files, [file1_path])

    def test_no_output_files_in_config(self):
        test_utils.create_file('file1.txt')

        downloadable_files = self.perform_execution(None)

        self.assertEqual([], downloadable_files)

    def test_output_files_with_parameter_substitution(self):
        file1 = test_utils.create_file('file1.txt', text='hello world')
        file2 = test_utils.create_file(os.path.join('sub', 'child', 'admin.log'), text='password=123')

        downloadable_files = self.perform_execution([
            os.path.join(test_utils.temp_folder, '${p1}.txt'),
            os.path.join(test_utils.temp_folder, 'sub', '${p2}', 'admin.log')],
            parameter_values={'p1': 'file1', 'p2': 'child'})

        self.assert_downloadable_files(downloadable_files, [file1, file2])

    def test_output_files_with_secure_parameters(self):
        test_utils.create_file('file1.txt', text='hello world')
        file2 = test_utils.create_file(os.path.join('sub', 'child', 'admin.log'), text='password=123')

        param1 = create_script_param_config('p1', secure=True)
        param2 = create_script_param_config('p2')

        downloadable_files = self.perform_execution([
            os.path.join(test_utils.temp_folder, '${p1}.txt'),
            os.path.join(test_utils.temp_folder, 'sub', '${p2}', 'admin.log')],
            parameter_values={'p1': 'file1', 'p2': 'child'},
            parameters=[param1, param2])

        self.assert_downloadable_files(downloadable_files, [file2])

    def perform_execution(self, output_files, parameter_values=None, parameters=None):
        if parameter_values is None:
            parameter_values = {}

        if parameters is None:
            parameters = [create_script_param_config(key) for key in parameter_values.keys()]

        config_model = create_config_model('my_script', output_files=output_files, parameters=parameters)
        config_model.set_all_param_values(parameter_values)

        user = User('userX', create_audit_names(ip='127.0.0.1'))
        execution_id = self.executor_service.start_script(
            config_model, user)
        self.executor_service.stop_script(execution_id, user)

        finish_condition = threading.Event()
        self.executor_service.add_finish_listener(lambda: finish_condition.set(), execution_id)
        finish_condition.wait(2)

        downloadable_files = self.feature.get_downloadable_files(execution_id)

        return downloadable_files

    def setUp(self):
        super().setUp()
        test_utils.setup()

        executor._process_creator = _MockProcessWrapper
        self.executor_service = ExecutionService(AnyUserAuthorizer(), _IdGeneratorMock(), test_utils.env_variables)

        self.feature = FileDownloadFeature(UserFileStorage(b'123456'), test_utils.temp_folder)
        self.feature.subscribe(self.executor_service)

    def tearDown(self):
        super().tearDown()
        test_utils.cleanup()

    def assert_downloadable_files(self, prepared_files, original_files):
        prepared_files_dict = {os.path.basename(f): f for f in prepared_files}
        original_files_dict = {os.path.basename(f): f for f in original_files}

        self.assertEqual(original_files_dict.keys(), prepared_files_dict.keys())

        for filename in original_files_dict.keys():
            prepared_file = prepared_files_dict[filename]
            original_file = original_files_dict[filename]

            prepared_content = file_utils.read_file(prepared_file)
            original_content = file_utils.read_file(original_file)

            self.assertEqual(original_content, prepared_content, 'Different content for file ' + filename)


def inline_image(path):
    return {'type': 'inline-image', 'path': path}


class TestInlineImages(unittest.TestCase):
    def setUp(self) -> None:
        test_utils.setup()

        executor._process_creator = _MockProcessWrapper
        self.executor_service = ExecutionService(AnyUserAuthorizer(), _IdGeneratorMock(), test_utils.env_variables)

        self.file_download_feature = file_download_feature.FileDownloadFeature(
            UserFileStorage(b'123456'), test_utils.temp_folder)
        self.file_download_feature.subscribe(self.executor_service)

        self.images = []

    def tearDown(self) -> None:
        test_utils.cleanup()

        executions = self.executor_service.get_active_executions('userX')
        for execution in executions:
            self.executor_service.kill_script(execution, User('userX', []))

    def _add_image(self, original_path, new_path):
        self.images.append((original_path, new_path))

    def test_single_static_image(self):
        path = test_utils.create_file('test.png')
        config = create_config_model('my_script', output_files=[inline_image(path)])

        execution_id = self.start_execution(config)

        self.write_output(execution_id, '123\n456')

        self.wait_output_chunks(execution_id, chunks_count=1)

        self.assert_images(path)

    def test_multiple_static_images(self):
        path1 = test_utils.create_file('test1.png')
        path2 = test_utils.create_file('test2.png')
        path3 = test_utils.create_file('test3.png')
        config = create_config_model('my_script',
                                     output_files=[inline_image(path1), inline_image(path2), inline_image(path3)])

        execution_id = self.start_execution(config)

        self.write_output(execution_id, '123\n' + '456')

        self.wait_output_chunks(execution_id, chunks_count=1)

        self.assert_images(path1, path2, path3)

    def test_single_static_image_when_multiple_outputs(self):
        path = test_utils.create_file('test.png')
        config = create_config_model('my_script', output_files=[inline_image(path)])

        execution_id = self.start_execution(config)

        self.write_output(execution_id, '123\n456')
        self.wait_output_chunks(execution_id, chunks_count=1)

        self.write_output(execution_id, '789\n0')
        self.wait_output_chunks(execution_id, chunks_count=2)

        self.assert_images(path)

    def test_single_dynamic_image(self):
        path = test_utils.create_file('test.png')
        config = create_config_model('my_script', output_files=[inline_image('##any_path.png#')])

        execution_id = self.start_execution(config)

        full_path = file_utils.normalize_path(path)
        self.write_output(execution_id, '123\n' + full_path + '\n456')
        self.wait_output_chunks(execution_id, chunks_count=1)

        self.assert_images(full_path)

    def test_single_dynamic_image_when_unnormalized(self):
        test_utils.create_file('sub/test.png')
        config = create_config_model('my_script', output_files=[inline_image('#([\.\w]+/)+\w+.png#')])

        execution_id = self.start_execution(config)

        unnormalized_path = os.path.join(test_utils.temp_folder, '.', 'sub', '..', 'sub', 'test.png')
        self.write_output(execution_id, '_ ' + unnormalized_path + ' _\n')
        self.wait_output_chunks(execution_id, chunks_count=1)

        image_keys = [img[0] for img in self.images]
        self.assertEqual([unnormalized_path], image_keys)

    def test_mixed_images_when_multiple_output(self):
        path1 = test_utils.create_file('test123.png')
        path2 = test_utils.create_file('images/test.png')
        path3 = test_utils.create_file('a.b.c.png')
        path4 = test_utils.create_file('test456.png')
        path5 = test_utils.create_file('some/long/path/me.jpg')

        config = create_config_model('my_script', output_files=[
            inline_image(test_utils.temp_folder + os_utils.path_sep() + '#test\d+.png#'),
            inline_image(path2),
            inline_image(path3),
            inline_image('##any_path/path/\w+#.jpg')
        ])

        execution_id = self.start_execution(config)

        paths = [normalize_path(p) for p in (path1, path2, path3, path4, path5)]
        for index, path in enumerate(paths):
            self.write_output(execution_id, '__ ' + path + ' __\n')
            self.wait_output_chunks(execution_id, chunks_count=index + 1)

        self.write_output(execution_id, '__ ' + path2 + ' __\n')
        self.wait_output_chunks(execution_id, chunks_count=len(paths) + 1)

        self.assert_images(*paths)

    def test_find_multiple_images_by_same_pattern(self):
        path1 = test_utils.create_file('test123.png')
        test_utils.create_file('images/test.png')
        path3 = test_utils.create_file('a.b.c.png')
        path4 = test_utils.create_file('some/sub/folder/test456.png')

        config = create_config_model('my_script', output_files=[
            inline_image('##any_path.png#')
        ])

        execution_id = self.start_execution(config)

        paths = [normalize_path(p) for p in (path1, path3, path4)]
        for index, path in enumerate(paths):
            self.write_output(execution_id, '__ ' + path + ' __\n')
            self.wait_output_chunks(execution_id, chunks_count=index + 1)

        self.assert_images(*paths)

    def test_image_path_split_in_chunks(self):
        path = test_utils.create_file('test123.png')

        config = create_config_model('my_script', output_files=[inline_image('##any_path.png#')])

        execution_id = self.start_execution(config)

        normalized = normalize_path(path)

        self.write_output(execution_id, normalized[:4])
        self.wait_output_chunks(execution_id, chunks_count=1)

        self.write_output(execution_id, normalized[4:] + '\n')
        self.wait_output_chunks(execution_id, chunks_count=2)

        self.assert_images(path)

    def test_image_path_split_in_chunks_and_no_newlines(self):
        path = test_utils.create_file('test123.png')

        config = create_config_model('my_script', output_files=[inline_image('##any_path.png#')])

        execution_id = self.start_execution(config)

        normalized = normalize_path(path)

        self.write_output(execution_id, normalized[:4])
        self.wait_output_chunks(execution_id, chunks_count=1)

        self.write_output(execution_id, normalized[4:])
        self.wait_output_chunks(execution_id, chunks_count=2)

        self.executor_service.get_active_executor(execution_id, DEFAULT_USER).process_wrapper.stop()
        self.wait_close(execution_id)

        self.assert_images(path)

    def wait_output_chunks(self, execution_id, *, chunks_count):
        waiter = OutputWaiter()
        self.executor_service.get_anonymized_output_stream(execution_id).subscribe(waiter)
        waiter.wait_chunks(chunks_count, timeout=0.5)

    def wait_close(self, execution_id):
        chunk_condition = threading.Condition()
        closed = False

        def waiter():
            global closed
            closed = True
            with chunk_condition:
                chunk_condition.notify_all()

        self.executor_service.get_anonymized_output_stream(execution_id).subscribe_on_close(waiter)
        with chunk_condition:
            chunk_condition.wait_for(lambda: closed, 0.5)

    def write_output(self, execution_id, output):
        process_wrapper = self.executor_service.get_active_executor(execution_id, DEFAULT_USER).process_wrapper
        process_wrapper.write_output(output)

    def start_execution(self, config):
        execution_id = self.executor_service.start_script(config, DEFAULT_USER)
        self.file_download_feature.subscribe_on_inline_images(execution_id, self._add_image)
        return execution_id

    def assert_images(self, *paths):
        normalized_paths = [file_utils.normalize_path(p) for p in paths]
        actual_paths = [file_utils.normalize_path(image[0]) for image in self.images]

        self.assertCountEqual(normalized_paths, actual_paths)


class OutputWaiter:
    def __init__(self) -> None:
        self.chunks = []
        self.chunk_condition = threading.Condition()

    def on_next(self, chunk):
        self.chunks.append(chunk)

        with self.chunk_condition:
            self.chunk_condition.notify_all()

    def on_close(self):
        pass

    def wait_chunks(self, chunk_count, *, timeout):
        with self.chunk_condition:
            result = self.chunk_condition.wait_for(lambda: len(self.chunks) >= chunk_count, timeout)

        if not result:
            raise Exception('Chunk count did not reach ' + str(chunk_count))
