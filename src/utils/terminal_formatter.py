from abc import ABC, abstractmethod
from collections import namedtuple, defaultdict

from react.observable import ReplayObservable

FORMAT_ESCAPE_CHARACTER = ''


class _CommandHandler(ABC):
    def __init__(self, min_arguments_count=1, max_arguments_count=1) -> None:
        super().__init__()
        self.min_arguments_count = min_arguments_count
        self.max_arguments_count = max_arguments_count

    def is_valid_arguments_count(self, count):
        return self.min_arguments_count <= count <= self.max_arguments_count

    @abstractmethod
    def handle(self, arguments, terminal):
        pass


class _SetGraphicsCommandHandler(_CommandHandler):
    def __init__(self) -> None:
        super().__init__(1, 10)

    def handle(self, arguments, terminal):
        reset_graphics = '0' in arguments
        if reset_graphics:
            terminal.reset_graphic_mode()

        for key in TEXT_COLOR_DICT:
            if key in arguments:
                terminal.set_text_color(TEXT_COLOR_DICT[key])
                break

        for key in BACKGROUND_COLOR_DICT:
            if key in arguments:
                terminal.set_background_color(BACKGROUND_COLOR_DICT[key])
                break

        if not reset_graphics:
            for key in TEXT_STYLES_DICT:
                zero_padded_key = '0' + key
                if (key in arguments) or (zero_padded_key in arguments):
                    terminal.add_style(TEXT_STYLES_DICT[key])

            for key in RESET_STYLES_DICT:
                if key in arguments:
                    terminal.remove_style(RESET_STYLES_DICT[key])


COMMAND_HANDLERS = {
    'm': _SetGraphicsCommandHandler(),
    'K': None,
    'H': None,
    'f': None,
    'A': None,
    'B': None,
    'C': None,
    'D': None
}

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

FormattedText = namedtuple('FormattedText',
                           ['text', 'text_color', 'background_color', 'styles'])


class TerminalPosition:

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def __gt__(self, another) -> bool:
        if self.y != another.y:
            return self.y > another.y
        return self.x > another.x

    def __lt__(self, another) -> bool:
        if self.y != another.y:
            return self.y < another.y
        return self.x < another.x

    def __le__(self, another) -> bool:
        return (self < another) or (self == another)

    def __ge__(self, another) -> bool:
        return (self > another) or (self == another)

    def __eq__(self, another: 'TerminalPosition') -> bool:
        return (another is not None) and (self.x == another.x) and (self.y == another.y)

    def set(self, x, y):
        self.x = x
        self.y = y

    def new_line(self):
        self.y += 1
        self.x = 0

    def inc_x(self, delta=1):
        self.x += delta

    def __repr__(self) -> str:
        return '(x=%d, y=%d)' % (self.x, self.y)

    def copy(self):
        return TerminalPosition(self.x, self.y)


class TerminalEmulator(object):
    def __init__(self, output_callback):
        self.buffer = ''
        self.command_buffer = ''
        self.modified_chunks = defaultdict(list)

        self.current_text_color = None
        self.current_background_color = None
        self.current_styles = []

        self.output_callback = output_callback

        self.max_cursor_position = TerminalPosition(0, 0)
        self.cursor_position = TerminalPosition(0, 0)
        self.modification_start_position = TerminalPosition(0, 0)

    def feed(self, output_chunk):
        output_chunk = output_chunk.replace('\r\n', '\n')
        for character in output_chunk:
            if self.command_buffer:
                self.command_buffer += character

                if len(self.command_buffer) == 2:
                    correct_command = (character == '[')

                elif (len(self.command_buffer) > 2) and (character in COMMAND_HANDLERS):
                    arguments = self._prepare_arguments(self.command_buffer[2:-1])

                    self.command_buffer = ''

                    self._handle_command(arguments, character)
                    correct_command = False

                else:
                    correct_command = character.isdigit() or (character == ';')

                if not correct_command:
                    self._append_to_buffer(self.command_buffer)
                    self.command_buffer = ''

            elif character == FORMAT_ESCAPE_CHARACTER:
                self._flush_buffer()

                self.command_buffer = character

            elif character == '\r':
                self._move_cursor(0, self.cursor_position.y)

            elif character == '\n':
                self._move_cursor(0, self.cursor_position.y + 1)

            else:
                self._append_to_buffer(character)

        if (self.modified_chunks or self.buffer) and not self.command_buffer:
            self._flush_buffer()

    def flush_remaining(self):
        if self.buffer or self.command_buffer or self.modified_chunks:
            self.buffer += self.command_buffer
            self._flush_buffer()

    def _append_to_buffer(self, text):
        if text:
            self.buffer += text
            self.cursor_position.inc_x(len(text))

    def to_formatted_text(self, text):
        return FormattedText(
            text,
            self.current_text_color,
            self.current_background_color,
            self.current_styles)

    def _prepare_arguments(self, arguments_text):
        arguments = arguments_text.split(';')

        prepared_arguments = []
        for arg in arguments:
            arg = arg.strip()
            if arg == '':
                arg = '0'

            prepared_arguments.append(arg)

        return prepared_arguments

    def _handle_command(self, arguments, command_character):
        handler = COMMAND_HANDLERS[command_character]
        if handler is None:
            return False

        if not handler.is_valid_arguments_count(len(arguments)):
            return False

        for arg in arguments:
            # string isdigit validates, that ALL characters are digits
            if not arg.isdigit():
                return False

        handler.handle(arguments, self)
        return True

    def _move_cursor(self, x, y):
        if not self.buffer and len(self.modified_chunks) == 1:
            prev_chunk = next(iter(self.modified_chunks.values()))[0]
            if y > prev_chunk['y'] or ((y == prev_chunk['y']) and (x >= prev_chunk['x_end'])):
                self.buffer = prev_chunk['text']
                self.modified_chunks.clear()

        new_position = TerminalPosition(x, y)

        if not self.buffer and not self.modified_chunks:
            self.modification_start_position = new_position

        if (not self.modified_chunks) \
                and (self.modification_start_position >= self.max_cursor_position) \
                and (new_position >= self.cursor_position):
            if y > self.cursor_position.y:
                self.buffer += '\n' * (y - self.cursor_position.y)
                self.buffer += ' ' * x
            else:
                self.buffer += ' ' * (x - self.cursor_position.x)

            self.cursor_position.set(x, y)
            return

        if not self.modified_chunks and '\n' in self.buffer:
            self._flush_buffer()
            self.cursor_position.set(x, y)
            self.modification_start_position = self.cursor_position.copy()
            return

        if self.buffer:
            self.add_modified_chunk(self.buffer)
            self.buffer = ''

        if y > self.max_cursor_position.y:
            for current_y in range(self.max_cursor_position.y, y + 1):
                line_chunks = self.modified_chunks[current_y]
                if not line_chunks:
                    line_chunks.append(self._create_buffer_chunk('', 0, current_y))

        self.cursor_position.set(x, y)

    def add_modified_chunk(self, text):
        new_chunk = self._create_buffer_chunk(text, self.cursor_position.x, self.cursor_position.y)
        to_remove = []
        line_chunks = self.modified_chunks[self.cursor_position.y]
        for another_chunk in reversed(line_chunks):
            another_start = another_chunk['x_start']
            new_start = new_chunk['x_start']
            new_end = new_chunk['x_end']
            another_end = another_chunk['x_end']
            another_text = another_chunk['text']
            new_text = new_chunk['text']

            if (another_start <= new_end) and (new_start <= another_end):
                min_start = min(another_start, new_start)
                max_end = max(another_end, new_end)

                if new_start <= another_start:
                    another_start_offset = new_end - another_start
                    text = new_text + another_text[another_start_offset:]
                else:
                    text = another_text[:new_start - another_start] + new_text
                    if another_end > new_end:
                        text += another_text[new_end - another_start:]

                new_chunk['x_start'] = min_start
                new_chunk['x_end'] = max_end
                new_chunk['text'] = text
                to_remove.append(another_chunk)

        for obsolete in to_remove:
            line_chunks.remove(obsolete)
        line_chunks.append(new_chunk)

    def _create_buffer_chunk(self, text, x_end, y):
        return {
            'text': text,
            'y': y,
            'x_start': x_end - len(text),
            'x_end': x_end}

    def _flush_buffer(self):
        if (len(self.buffer) == 0) and (not self.modified_chunks):
            return

        current_buffer = self.buffer
        self.buffer = ''

        def send_data(text, start_position):
            if len(text) == 0:
                return

            if start_position >= self.max_cursor_position:
                custom_position = None
            else:
                custom_position = start_position
            formatted_text = self.to_formatted_text(text)
            self.output_callback(formatted_text, custom_position)

        if not self.modified_chunks:
            while current_buffer.startswith('\n') and self.modification_start_position.y <= self.max_cursor_position.y:
                self.modification_start_position.new_line()
                current_buffer = current_buffer[1:]

            send_data(current_buffer, self.modification_start_position)
            self.modification_start_position = self.cursor_position.copy()
            self.max_cursor_position = max(self.max_cursor_position, self.cursor_position.copy())
            return

        self.add_modified_chunk(current_buffer)

        modified_lines = sorted(self.modified_chunks.keys())
        last_line = modified_lines[-1]
        previous_line = None
        previous_x = 0
        current_text = ''
        current_position = None
        for line in modified_lines:
            if (previous_line is not None) and ((previous_line + 1) != line):
                send_data(current_text, current_position)
                current_text = ''
                current_position = None

            previous_x = 0
            for chunk in self.modified_chunks[line]:
                if current_position is None:
                    current_position = TerminalPosition(chunk['x_start'], line)
                elif chunk['x_start'] != previous_x:
                    send_data(current_text, current_position)
                    current_text = ''
                    current_position = None
                    continue

                previous_x = chunk['x_end']
                current_text += chunk['text']

            if (line >= self.max_cursor_position.y) and (line != last_line):
                current_text += '\n'

            previous_line = line

        if current_text:
            send_data(current_text, current_position)

        self.modified_chunks.clear()

        self.modification_start_position = self.cursor_position.copy()
        self.max_cursor_position = max(TerminalPosition(previous_x, previous_line), self.max_cursor_position)

    def reset_graphic_mode(self):
        self.current_text_color = None
        self.current_background_color = None
        self.current_styles = []

    def add_style(self, style):
        if style not in self.current_styles:
            self.current_styles.append(style)

    def remove_style(self, style):
        self.current_styles.remove(style)

    def set_text_color(self, color):
        self.current_text_color = color

    def set_background_color(self, color):
        self.current_background_color = color


TerminalOutputChunk = namedtuple('TerminalOutputChunk',
                                 ['formatted_text', 'custom_position'])


class TerminalOutputTransformer(ReplayObservable):

    def __init__(self, source_observable):
        super().__init__()

        self._terminal_emulator = TerminalEmulator(self.terminal_callback)
        source_observable.subscribe(self)

    def on_next(self, data):
        self._terminal_emulator.feed(data)

    def on_close(self):
        self._terminal_emulator.flush_remaining()
        self._close()

    def terminal_callback(self, formatted_text, custom_position):
        self._push(TerminalOutputChunk(formatted_text, custom_position))
