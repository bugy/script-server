import unittest

from utils.terminal_formatter import TerminalEmulator, FormattedText, TerminalOutputChunk, TerminalPosition

FORMAT_ESCAPE_CHARACTER = ''


class TerminalFormatterTest(unittest.TestCase):
    def test_simple_text(self):
        self._feed('some text')

        self.assertListEqual(['some text'], self._get_output_texts())

    def test_simple_multiple_chunks(self):
        self._feed('some text')
        self._feed('another text')
        self._feed('1')

        self.assertListEqual(['some text', 'another text', '1'], self._get_output_texts())

    def test_simple_red_text(self):
        self._feed('[31msome text')

        self.assertListEqual([self._output_chunk('some text', text_color='red')],
                             self._get_output())

    def test_formatting_with_reset_code(self):
        self._feed('[0;1;42;97msome text')

        self.assertListEqual([self._output_chunk('some text', text_color='white', background_color='green')],
                             self._get_output())

    def test_caret_return_inside_chunk(self):
        self._feed('some\rtext')

        self.assertListEqual([self._output_chunk('text')],
                             self._get_output())

    def test_caret_return_between_chunks(self):
        self._feed('some text\r')
        self._feed('123')

        self.assertListEqual([self._output_chunk('some text'), self._output_chunk('123', custom_position=(0, 0))],
                             self._get_output())

    def test_caret_return_and_new_line(self):
        self._feed('some text\r\n123')

        self.assertListEqual([self._output_chunk('some text\n123')],
                             self._get_output())

    def test_caret_return_and_new_line_when_separate_chunks(self):
        self._feed('some text\r\n')
        self._feed('123')

        self.assertListEqual([self._output_chunk('some text\n'), self._output_chunk('123')],
                             self._get_output())

    def test_text_cr_and_then_multiline_starting_chunk(self):
        self._feed('some text\r')
        self._feed('\n\n\n123')

        self.assertListEqual([self._output_chunk('some text'), self._output_chunk('\n\n\n123')],
                             self._get_output())

    def test_cr_lf_text_cr_and_chunk(self):
        self._feed('some text\r\n123\r')
        self._feed('987')

        self.assertListEqual([self._output_chunk('some text\n123'),
                              self._output_chunk('987', custom_position=(0, 1))],
                             self._get_output())

    def test_multiple_lines_with_cr_lf_in_single_chunk(self):
        self._feed('line1\r\nline2\r\nline3\r\n')

        self.assertListEqual([self._output_chunk('line1\nline2\nline3\n')],
                             self._get_output())

    def test_multiple_lines_with_cr_lf_in_multiple_chunks(self):
        self._feed('line1\r\n')
        self._feed('line2\r\n')
        self._feed('line3\r\n')

        self.assertListEqual([self._output_chunk('line1\n'),
                              self._output_chunk('line2\n'),
                              self._output_chunk('line3\n')],
                             self._get_output())

    def test_multiple_new_lines_as_single_chunk(self):
        self._feed('\n\n\n')

        self.assertListEqual([self._output_chunk('\n\n\n')],
                             self._get_output())

    def test_multiple_new_lines_as_multiple_chunks(self):
        self._feed('\n')
        self._feed('\n')
        self._feed('\n')

        self.assertListEqual([self._output_chunk('\n'), self._output_chunk('\n'), self._output_chunk('\n')],
                             self._get_output())

    def _output_chunk(self, text, *, text_color=None, background_color=None, styles=None, custom_position=None):
        if styles is None:
            styles = []

        formatted_text = FormattedText(text=text,
                                       text_color=text_color,
                                       background_color=background_color,
                                       styles=styles)
        if custom_position is not None:
            custom_position = TerminalPosition(*custom_position)

        return TerminalOutputChunk(formatted_text, custom_position)

    def setUp(self):
        super().setUp()

        self.output = []
        self.terminal = TerminalEmulator(lambda text, position: self.output.append(TerminalOutputChunk(text, position)))

    def _feed(self, chunk):
        self.terminal.feed(chunk)

    def _get_output(self):
        self.terminal.flush_remaining()

        result = []
        result.extend(self.output)

        return result

    def _get_output_texts(self):
        return [terminal_chunk.formatted_text.text for terminal_chunk in self._get_output()]
