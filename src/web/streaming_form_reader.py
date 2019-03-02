import os
from collections import namedtuple

from utils import file_utils
from utils.collection_utils import put_multivalue
from utils.tornado_utils import parse_header


class _FormDataPart:
    def __init__(self, header, files_path):
        header_str = header.decode('utf-8')
        if '\r\n' in header_str:
            header_str = header_str[:header_str.index('\r\n')]

        (value, sub_headers) = parse_header(header_str)

        self.name = sub_headers['name']

        self.filename = sub_headers.get('filename')

        if self.filename:
            self.path = os.path.join(files_path, self.filename)
            self.path = file_utils.create_unique_filename(self.path)
            # touch file
            open(self.path, 'w').close()
        else:
            self.value = ''

    def write(self, chunk):
        if self.filename:
            with open(self.path, 'ab') as f:
                f.write(chunk)
            return

        self.value += chunk.decode('utf-8')


HttpFormFile = namedtuple('HttpFormFile', ['filename', 'path'])


class StreamingFormReader:

    def __init__(self, headers, output_files_path) -> None:
        (content_type, content_type_dict) = parse_header(headers.get('Content-Type'))

        content_length = headers.get('Content-Length')
        self.max_length = int(content_length) if content_length else 0

        if content_type != 'multipart/form-data':
            raise Exception('Unsupported content type: ' + content_type)

        if 'boundary' not in content_type_dict:
            raise Exception('Failed to find boundary in header ' + content_type)

        self._boundary = b'--' + content_type_dict['boundary'].encode('utf-8')
        self._fields_separator = b'\r\n' + self._boundary
        self._buffer = b''
        self._current_part = None
        self._output_files_path = output_files_path
        self._read_bytes = 0
        self.values = {}
        self.files = {}

    def read(self, chunk):
        if self._reached_end():
            return

        self._buffer += chunk

        self._read_bytes += len(chunk)

        if not self._reached_end() and len(self._buffer) < 128:
            return

        count = 0

        while self._buffer and count < 10000:
            count += 1

            if not self._current_part:
                if b'\r\n\r\n' not in self._buffer:
                    break

                if not self._buffer.startswith(self._boundary):
                    raise Exception('Invalid buffer format: ' + str(self._buffer))

                part = self._buffer[len(self._fields_separator):]

                (header, self._buffer) = part.split(b'\r\n\r\n', 1)

                self._current_part = _FormDataPart(header, self._output_files_path)

            if self._fields_separator not in self._buffer:
                potential_separator_start = self._find_potential_separator_start(self._buffer)

                if potential_separator_start >= 0:
                    body = self._buffer[:potential_separator_start]
                    self._buffer = self._buffer[potential_separator_start:]
                else:
                    body = self._buffer
                    self._buffer = b''

                self._current_part.write(body)
                break

            body_end = self._buffer.index(self._fields_separator)
            body = self._buffer[:body_end]
            self._buffer = self._buffer[body_end + 2:]

            self._current_part.write(body)
            self._add_value(self._current_part)
            self._current_part = None

        if self._reached_end():
            if self._current_part:
                self._current_part.write(self._buffer)
                self._buffer = b''
                self._add_value(self._current_part)
                self._current_part = None

    def _reached_end(self):
        return (self.max_length > 0) and self._read_bytes >= self.max_length

    def _add_value(self, part):
        name = part.name

        if part.filename:
            new_value = HttpFormFile(part.filename, part.path)
            values_dict = self.files
        else:
            new_value = part.value
            values_dict = self.values

        put_multivalue(values_dict, name, new_value)

    def _find_potential_separator_start(self, text):
        offset = max(0, len(text) - len(self._fields_separator))
        ending = text[offset:]

        next_start = 0

        while next_start < len(ending):
            possible_separator_start = ending.find(self._fields_separator[0], next_start)
            if possible_separator_start < 0:
                return -1

            char_index = 1
            matches = True
            while (possible_separator_start + char_index) < len(ending):
                if ending[possible_separator_start + char_index] != self._fields_separator[char_index]:
                    matches = False
                    break
                char_index += 1

            if matches:
                return offset + possible_separator_start

            next_start = possible_separator_start + 1

        return -1
