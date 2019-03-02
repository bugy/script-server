import os
import unittest

import requests
from parameterized import parameterized_class
from urllib3._collections import HTTPHeaderDict

from tests import test_utils
from tests.test_utils import assert_large_dict_equal
from utils import file_utils, tornado_utils
from utils.collection_utils import put_multivalue, find_any
from web.streaming_form_reader import StreamingFormReader, HttpFormFile

_SINGLE_CHUNK = 'single_chunk'
_CHUNK_PER_FIELD = 'chunk_per_field'

_UPLOADS_FOLDER = os.path.join(test_utils.temp_folder, 'uploads')


@parameterized_class(('chunk_size'), [
    (_SINGLE_CHUNK,),
    (_CHUNK_PER_FIELD,),
    ('chunk_size_200',),
    ('chunk_size_20',),
    ('chunk_size_5',),
    ('chunk_size_1',)])
class StreamingFormReaderTest(unittest.TestCase):

    def test_empty_body(self):
        request = _prepare_request()

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({}, reader.values)
        self.assertEqual({}, reader.files)

    def test_single_value(self):
        request = _prepare_request(data={'param1': 'hello'})

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({'param1': 'hello'}, reader.values)
        self.assertEqual({}, reader.files)

    def test_multiple_values(self):
        request = _prepare_request(data={
            'param1': 5,
            'param2': True,
            'param3': 'Some very long string',
            'param4': '',
            'param5': 'Another string'
        })

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({
            'param1': '5',
            'param2': 'True',
            'param3': 'Some very long string',
            'param4': '',
            'param5': 'Another string'
        }, reader.values)
        self.assertEqual({}, reader.files)

    def test_repeating_value(self):
        data = HTTPHeaderDict()
        data.add('p1', 'abc')
        data.add('x', 'def')
        data.add('p1', 'x')
        data.add('x', '-1239-')
        data.add('x', '!@#$%^&*()_+')
        data.add('x', '.')
        data.add('another_param', '987654321')

        request = _prepare_request(data=data)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({
            'p1': ['abc', 'x'],
            'x': ['def', '-1239-', '!@#$%^&*()_+', '.'],
            'another_param': '987654321'
        }, reader.values)
        self.assertEqual({}, reader.files)

    def test_single_file(self):
        files = {'file_param': ('test.log', 'my very important data')}
        request = _prepare_request(files=files)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({}, reader.values)
        self._assert_files(files, reader.files)

    def test_large_single_file(self):
        files = {'tiny': ('huge.log', ('very very long file' * 10000).encode('utf-8'))}
        request = _prepare_request(files=files)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self._assert_files(files, reader.files)

    def test_files_with_complex_header(self):
        files = {}
        for i in range(1, 3):
            index = str(i)
            files['file ' + index] = (index + ' .log',
                                      'hello world ' + index,
                                      'application/rtf',
                                      {'CustomHeader1': 'my_header_val',
                                       'CustomHeader2': 'my_header_val2'})

        request = _prepare_request(files=files)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self._assert_files(files, reader.files)

    def test_multiple_files(self):
        files = {'file1': ('test.log', 'my very important data'),
                 'file2': ('passwords', ''),
                 'file3': ('game.exe', b'123456789 x123 Fu\x00dfb\x00e4lle')}
        request = _prepare_request(files=files)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual({}, reader.values)
        self._assert_files(files, reader.files)

    def test_files_and_parameters(self):
        files = {'file1': ('long_file.txt', ('some very very long text' * 10).encode('utf-8')),
                 'file2': ('symbols',
                           '~𝘈Ḇ𝖢𝕯٤ḞԍНǏ𝙅ƘԸⲘ𝙉০Ρ𝗤Ɍ𝓢ȚЦ𝒱Ѡ𝓧ƳȤѧᖯć𝗱ễ𝑓𝙜Ⴙ𝞲𝑗𝒌'
                           'ļṃŉо𝞎𝒒ᵲꜱ𝙩ừ𝗏ŵ𝒙𝒚ź1234567890!@#$%^&*()-_=+[{]};:",<.>/?'),
                 'file3': ('test_unicodes', '123456789 x123 Fu\x00dfb\x00e4lle')}
        data = {'symbols': '!@#%^',
                'file1': 'some filename.dat',
                'param1': 'hello world'}
        request = _prepare_request(files=files, data=data)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual(data, reader.values)
        self._assert_files(files, reader.files)

    def test_a_lot_of_files_and_parameters(self):
        files = {}
        data = {}

        for i in range(1, 500):
            index = str(i)

            files['file' + index] = ('my_file' + index + '.txt', ('content' + index) * 10)
            data['param' + index] = 'hello world x' + index

        request = _prepare_request(files=files, data=data)

        reader = _create_reader(request)
        self._read_body(reader, request)

        assert_large_dict_equal(data, reader.values, self)
        self._assert_files(files, reader.files)

    def test_read_chunk_after_max_length(self):
        data = {'param1': 'val', 'param2': '9876'}
        request = _prepare_request(data=data)

        reader = _create_reader(request)
        self._read_body(reader, request)
        self._read_body(reader, request)

        self.assertEqual(data, reader.values)

    def test_read_reach_max_length(self):
        data = {'param1': 'val', 'param2': '9876'}
        request = _prepare_request(data=data)

        reader = _create_reader(request)

        last_boundary_start = request.body.decode('utf-8').rfind('\r\n--')
        cut_length = len(request.body) - last_boundary_start
        new_suffix = b'x' * cut_length
        request.body = request.body[:last_boundary_start] + (new_suffix * 2)

        self._read_body(reader, request)

        expected_value1 = data.get('param1')
        expected_value2 = data.get('param2')
        actual_value1 = reader.values.get('param1')
        actual_value2 = reader.values.get('param2')

        if actual_value1 is not None and actual_value1.startswith('valx'):
            self._assert_start_with(expected_value1 + new_suffix.decode('utf-8'), actual_value1)
            self.assertEqual(expected_value2, actual_value2)
        else:
            self._assert_start_with(expected_value2 + new_suffix.decode('utf-8'), actual_value2)
            self.assertEqual(expected_value1, actual_value1)

    def test_mix_large_files_and_parameters(self):
        full_data = {}
        files = {}

        for i in range(0, 3):
            i_str = str(i)

            data = {'paramX' + i_str: 'val' + i_str, 'paramY' + i_str: 'my long val ' + i_str}
            full_data.update(data)

            files['fileA_' + i_str] = ('my_file' + i_str + '.txt', ('large_content_' + i_str) * (5 - i) * 500)
            files['fileB_' + i_str] = ('server_' + i_str + '.log', 'content_' + i_str)

        request = _prepare_request(data=full_data, files=files)
        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual(full_data, reader.values)
        self._assert_files(files, reader.files)

    def test_filename_collision_single_request(self):
        files = {'fileA': ('collision.txt', 'AAA'),
                 'fileB': ('collision.txt', 'BBB'),
                 'fileC': ('collision.txt', 'CCC')}

        request = _prepare_request(files=files)
        reader = _create_reader(request)
        self._read_body(reader, request)

        expected_names = ['collision.txt', 'collision_0.txt', 'collision_1.txt']
        expected_path_names = self._build_expected_path_names(expected_names, files.keys(), reader.files)

        self._assert_files(files, reader.files, expected_path_names)

    def test_filename_collision_multiple_requests(self):
        for i, suffix in enumerate(['A', 'BB', 'C', 'DDD', 'EF']):
            first_key = 'fileX_' + suffix
            second_key = 'fileY_' + suffix
            files = {first_key: ('collision.txt', suffix * 5),
                     second_key: ('normal_file_' + suffix + '.txt', 'hello ' + suffix)}
            request = _prepare_request(files=files)
            reader = _create_reader(request)
            self._read_body(reader, request)

            if i == 0:
                self._assert_files(files, reader.files)
                continue

            expected_path_names = {first_key: 'collision_' + str(i - 1) + '.txt',
                                   second_key: 'normal_file_' + suffix + '.txt'}

            self._assert_files(files, reader.files, expected_path_names)

    def test_repeating_files(self):
        files = HTTPHeaderDict()
        files.add('fileA', ('a.txt', 'AAA'))
        files.add('f1', ('b.txt', 'BBB'))
        files.add('fileA', ('c.txt', 'CCC'))

        request = _prepare_request(files=files)
        reader = _create_reader(request)
        self._read_body(reader, request)

        self._assert_files(files, reader.files)

    def test_single_value_similar_to_boundary(self):
        placeholder = 'x' * 35  # default boundary length -1
        request = _prepare_request(data={'param1': placeholder})

        reader = _create_reader(request)

        boundary = self._get_boundary(request)
        new_value = b'\r\n' + boundary[:-1]
        request.body = request.body.replace(placeholder.encode('utf-8'), new_value)

        self._read_body(reader, request)

        self.assertEqual({'param1': new_value.decode('utf-8')}, reader.values)

    def test_multiple_values_similar_to_boundary(self):
        boundary_length = 36
        data = {}
        placeholders = []
        for i in range(0, boundary_length):
            char = chr(48 + i)
            placeholder = char * boundary_length
            placeholders.append(placeholder)
            data['param' + char] = placeholder

        request = _prepare_request(data=data)

        reader = _create_reader(request)

        boundary = b'\r\n' + self._get_boundary(request)

        expected_values = {}
        index = 0
        for key, placeholder in data.items():
            new_value = boundary[:index] + b'#' + boundary[index + 1:]
            request.body = request.body.replace(placeholder.encode('utf-8'), new_value)
            expected_values[key] = new_value.decode('utf-8')
            index += 1

        self._read_body(reader, request)

        self.assertEqual(expected_values, reader.values)

    def test_special_characters_as_values(self):
        data = {'param1': ';', 'param2': '\r\n', 'param3': '--', }
        request = _prepare_request(data=data)

        reader = _create_reader(request)
        self._read_body(reader, request)

        self.assertEqual(data, reader.values)

    def _build_expected_path_names(self, expected_names, expected_keys, actual_files):
        expected_path_names = {}
        for key, file in actual_files.items():
            real_name = os.path.basename(file.path)
            if (real_name in expected_names) and (key in expected_keys):
                expected_names.remove(real_name)
                expected_path_names[key] = real_name
            else:
                self.fail('Unexpected filename ' + real_name + '. All files: ' + str(actual_files))
        return expected_path_names

    def _read_body(self, reader, request):
        body = request.body

        if (self.chunk_size == _SINGLE_CHUNK) or not body:
            reader.read(body)
            return

        if self.chunk_size == _CHUNK_PER_FIELD:
            self.read_by_chunks(body, reader, request)
            return

        chunk_size = int(self.chunk_size[len('chunk_size_'):])
        read_bytes = 0
        while read_bytes < len(body):
            chunk = body[read_bytes:read_bytes + chunk_size]

            reader.read(chunk)

            read_bytes += len(chunk)

            if len(chunk) == 0:
                break

    def read_by_chunks(self, body, reader, request):
        boundary = b'\r\n' + self._get_boundary(request)
        parts = body.split(boundary)

        epilogue = b'--\r\n'
        add_epilogue = False
        if parts and (parts[-1] == epilogue):
            add_epilogue = True
            del parts[-1]

        for part in parts:
            if parts.index(part) > 0:
                part = boundary + part

            reader.read(part)

        if add_epilogue:
            reader.read(boundary + epilogue)
        else:
            reader.read(boundary)

    def _get_boundary(self, request):
        (_, header_params) = tornado_utils.parse_header(request.headers['Content-Type'])
        boundary = ('--' + header_params['boundary']).encode('utf-8')
        return boundary

    def _assert_files(self, expected_files, actual_files, expected_path_names=None):
        if expected_path_names is None:
            expected_path_names = {}

        expected_form_files = {}
        for key, file in expected_files.items():
            if key in expected_path_names:
                path_name = expected_path_names[key]
            else:
                path_name = file[0]

            form_file = HttpFormFile(file[0], os.path.join(_UPLOADS_FOLDER, path_name))

            put_multivalue(expected_form_files, key, form_file)

        self.assertEqual(expected_form_files, actual_files)

        for key, file in expected_files.items():
            actual_file = actual_files[key]
            if isinstance(actual_file, list):
                actual_file = find_any(actual_file, lambda f: f.filename == file[0])
                if actual_file is None:
                    self.fail('Failed to find actual file for ' + str(file))

            actual_path = actual_file.path
            expected_content = file[1]

            byte_content = isinstance(expected_content, bytes)
            actual_content = file_utils.read_file(actual_path, byte_content=byte_content)

            self.assertEqual(expected_content, actual_content)

    def _assert_start_with(self, expected_prefix, actual_text):
        self.assertTrue(actual_text.startswith(expected_prefix),
                        'Expected ' + actual_text + ' to start with ' + expected_prefix)

    def setUp(self):
        test_utils.setup()

        os.makedirs(_UPLOADS_FOLDER)

    def tearDown(self):
        test_utils.cleanup()

        if os.path.exists(_UPLOADS_FOLDER):
            test_utils._rmtree(_UPLOADS_FOLDER)


def _prepare_request(files=None, data=None):
    if not files:
        files = [('notafile', None)]

    prepare = requests.Request('POST', 'http://nowhere', files=files, data=data).prepare()

    return prepare


def _create_reader(request):
    return StreamingFormReader(request.headers, _UPLOADS_FOLDER)
