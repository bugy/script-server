import copy
import re


class FormattedText(object):
    text = None
    text_color = None
    background_color = None
    styles = []

    def __init__(self, text, text_color, background_color, styles):
        self.text = text
        self.text_color = text_color
        self.background_color = background_color
        self.styles = copy.copy(styles)


class BashReader(object):
    buffer = ''
    command_buffer = ''

    current_text_color = None
    current_background_color = None
    current_styles = []

    def __init__(self):
        self.current_styles = []

    def read(self, process_output_chunk):
        result = []

        for character in process_output_chunk:
            if self.command_buffer:
                self.command_buffer += character

                bash_format = is_bash_format_start(self.command_buffer)
                if not bash_format:
                    self.buffer += self.command_buffer
                    self.command_buffer = ''

                elif self.command_buffer.endswith('m'):
                    command = self.command_buffer[2:-1]
                    if command and (command != '0'):
                        subcommands = command.split(';')

                        for key in TEXT_COLOR_DICT:
                            if key in subcommands:
                                self.current_text_color = TEXT_COLOR_DICT[key]
                                break

                        for key in BACKGROUND_COLOR_DICT:
                            if key in subcommands:
                                self.current_background_color = BACKGROUND_COLOR_DICT[key]
                                break

                        for key in TEXT_STYLES_DICT:
                            zero_padded_key = '0' + key
                            if (key in subcommands) or (zero_padded_key in subcommands):
                                style = TEXT_STYLES_DICT[key]
                                if not style in self.current_styles:
                                    self.current_styles.append(style)

                        for key in RESET_STYLES_DICT:
                            if key in subcommands:
                                style = RESET_STYLES_DICT[key]
                                self.current_styles.remove(style)


                    else:
                        self.current_text_color = None
                        self.current_background_color = None
                        self.current_styles = []

                    self.command_buffer = ''

                elif self.command_buffer.endswith('K'):
                    self.command_buffer = ''

            elif character == FORMAT_ESCAPE_CHARACTER:
                if self.buffer:
                    result.append(self.get_current_text())
                    self.buffer = ''

                self.command_buffer += character

            else:
                self.buffer += character

        if self.buffer and not self.command_buffer:
            result.append(self.get_current_text())
            self.buffer = ''

        return result

    def get_current_text(self):
        if self.buffer or self.command_buffer:
            return FormattedText(
                self.buffer + self.command_buffer,
                self.current_text_color,
                self.current_background_color,
                self.current_styles)

        return None


FORMAT_ESCAPE_CHARACTER = ''
TEXT_COLOR_DICT = {
    '39': None,
    '31': 'red',
    '30': 'black',
    '32': 'green',
    '33': 'yellow',
    '34': 'blue',
    '35': 'magenta',
    '36': 'cyan',
    '37': 'lightgray',
    '90': 'darkgray',
    '91': 'lightred',
    '92': 'lightgreen',
    '93': 'lightyellow',
    '94': 'lightblue',
    '95': 'lightmagenta',
    '96': 'lightcyan',
    '97': 'white'
}

BACKGROUND_COLOR_DICT = {
    '49': None,
    '41': 'red',
    '40': 'black',
    '42': 'green',
    '43': 'yellow',
    '44': 'blue',
    '45': 'magenta',
    '46': 'cyan',
    '47': 'lightgray',
    '100': 'darkgray',
    '101': 'lightred',
    '102': 'lightgreen',
    '103': 'lightyellow',
    '104': 'lightblue',
    '105': 'lightmagenta',
    '106': 'lightcyan',
    '107': 'white'
}

TEXT_STYLES_DICT = {
    '1': 'bold',
    '2': 'dim',
    '4': 'underlined',
    '8': 'hidden',
}

RESET_STYLES_DICT = {
    '21': 'bold',
    '22': 'dim',
    '24': 'underlined',
    '28': 'hidden'
}


def is_bash_format_start(text):
    next_expected = FORMAT_ESCAPE_CHARACTER

    for c in text:
        if not re.match(next_expected, c):
            return False

        if c == FORMAT_ESCAPE_CHARACTER:
            next_expected = '\['
        elif c == '[':
            next_expected = '\d|K|m'
        elif c.isdigit():
            next_expected = '\d|;|m'
        elif c == ';':
            next_expected = '\d'
        elif (c == 'm') or (c == 'K'):
            # it should be the last symbol, so nothing is expected
            next_expected = ''

    return True
