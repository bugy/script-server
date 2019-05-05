import unittest

from utils.tornado_utils import parse_header


class TestParseHeader(unittest.TestCase):
    def test_simple_header(self):
        (header, subheaders) = parse_header('Content-Type: text/html')
        self.assertEqual('text/html', header)
        self.assertEqual({}, subheaders)

    def test_header_with_single_subheader(self):
        (header, subheaders) = parse_header('Content-Type: text/html; charset=UTF-8')
        self.assertEqual('text/html', header)
        self.assertEqual({'charset': 'UTF-8'}, subheaders)

    def test_header_with_multiple_subheaders(self):
        (header, subheaders) = parse_header('Content-Type: multipart/form-data; boundary=something; charset=UTF-8')
        self.assertEqual('multipart/form-data', header)
        self.assertEqual({'charset': 'UTF-8', 'boundary': 'something'}, subheaders)

    def test_header_with_subheader_without_val(self):
        (header, subheaders) = parse_header('Content-Type: multipart/form-data; crossorigin; charset=UTF-8')
        self.assertEqual('multipart/form-data', header)
        self.assertEqual({'charset': 'UTF-8', 'crossorigin': ''}, subheaders)

    def test_subheader_with_quotes(self):
        (header, subheaders) = parse_header('Content-Type: text/html; charset="UTF-8"')
        self.assertEqual('text/html', header)
        self.assertEqual({'charset': 'UTF-8'}, subheaders)

    def test_semicolon_inside_quotes(self):
        (header, subheaders) = parse_header('Content-Type: "text/html;"; charset=";UTF-8"; boundary=\';"hell";o;\'')
        self.assertEqual('text/html;', header)
        self.assertEqual({'charset': ';UTF-8', 'boundary': ';"hell";o;'}, subheaders)

    def test_strip_whitespaces(self):
        (header, subheaders) = parse_header(' Content-Type :text/html  '
                                            ';charset =  "UTF-8";crossorigin;'
                                            '   boundary  = something  ')
        self.assertEqual('text/html', header)
        self.assertEqual({
            'charset': 'UTF-8',
            'crossorigin': '',
            'boundary': 'something'}, subheaders)
