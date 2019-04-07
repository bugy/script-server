import {arraysEqual, contains, isEmptyArray, isNull, removeElement} from '../../common';

const DIGITS = new Set(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']);

function isDigit(char) {
    return DIGITS.has(char);
}

function addUniqueSortedInt(arr, value, start, end) {
    const length = arr.length;
    if (start >= length) {
        arr.push(value);
        return;
    }

    if (start >= end) {
        const existing = arr[start];
        if (existing < value) {
            arr.splice(start + 1, 0, value);
        } else if (existing > value) {
            arr.splice(start, 0, value);
        }
        return;
    }

    const mid = Math.floor((end + start) / 2);
    const midValue = arr[mid];
    if (midValue === value) {
        return;
    }

    if (midValue < value) {
        addUniqueSortedInt(arr, value, mid + 1, end);
    } else {
        addUniqueSortedInt(arr, value, start, mid - 1);
    }
}

export class TerminalModel {
    constructor() {
        this.listeners = [];

        this.clear();
    }

    addListener(listener) {
        this.listeners.push(listener);
    }

    write(text) {
        this.buffer += text;
        let lastReadIndex = 0;

        let commandBuffer = null;
        let currentText = '';

        for (let i = 0; i < this.buffer.length; i++) {
            const char = this.buffer[i];

            if (commandBuffer !== null) {
                commandBuffer += char;

                let correctCommand = true;
                if (commandBuffer.length === 2) {
                    correctCommand = (char === '[');
                } else if ((commandBuffer.length > 2) && (COMMAND_HANDLERS.has(char))) {
                    const args = prepareArguments(commandBuffer.substr(2, commandBuffer.length - 3));

                    commandBuffer = null;

                    this.handleCommand(args, char);

                    correctCommand = false;
                } else {
                    correctCommand = isDigit(char) || (char === ';');
                }

                if (!correctCommand) {
                    if (commandBuffer !== null) {
                        this.flushText(commandBuffer);
                        commandBuffer = null;
                    }

                    lastReadIndex = i;
                }

            } else if (char === FORMAT_ESCAPE_CHARACTER) {
                this.flushText(currentText);
                currentText = '';

                commandBuffer = char;

            } else if (char === '\n') {
                this.flushText(currentText);
                currentText = '';

                this.currentPosition = 0;
                this.currentLine++;
                this.maxLine = Math.max(this.maxLine, this.currentLine);

                lastReadIndex = i;

            } else if (char === '\r') {
                this.flushText(currentText);
                currentText = '';

                this.currentPosition = 0;
                lastReadIndex = i;

            } else {
                currentText += char;
                lastReadIndex = i;
            }
        }

        this.flushText(currentText);
        this.buffer = this.buffer.substr(lastReadIndex + 1);

        const changedLines = this.changedLines;
        this.changedLines = [];

        if (changedLines.length > 0) {
            for (const listener of this.listeners) {
                listener.linesChanges(changedLines);
            }
        }
    }

    clear() {
        this.lines = [];
        this.lineStyles = new Map();

        this.currentLine = 0;
        this.currentPosition = 0;
        this.maxLine = 0;

        this.buffer = '';

        this.currentStyle = null;

        this.changedLines = [];

        this.savedCursorPosition = null;

        for (const listener of this.listeners) {
            listener.cleared();
        }
    }

    clearFullLine() {
        this.lines[this.currentLine] = '';
        this.addChangedLine(this.currentLine);
    }

    clearLineToRight() {
        const line = this.getLine(this.currentLine);

        if (line.length <= this.currentPosition) {
            return;
        }

        this.lines[this.currentLine] = line.substring(0, this.currentPosition);
        this.addChangedLine(this.currentLine);
    }

    clearLineToLeft() {
        if (this.currentPosition === 0) {
            return;
        }

        const line = this.getLine(this.currentLine);
        if (line.length <= this.currentPosition) {
            this.lines[this.currentLine] = '';
            this.addChangedLine(this.currentLine);
            return;
        }

        const spaces = ' '.repeat(this.currentPosition);
        this.lines[this.currentLine] = spaces + line.substring(this.currentPosition);
        this.addChangedLine(this.currentLine);
    }

    getStyle(line) {
        return this.lineStyles.get(line);
    }

    flushText(text) {
        if (text.length === 0) {
            return;
        }

        const line = this.getLine(this.currentLine);
        this.lines[this.currentLine] = replaceAt(line, this.currentPosition, text);

        const end = this.currentPosition + text.length;
        this.updateTextStyle(this.currentLine, this.currentPosition, end, this.currentStyle);

        this.currentPosition = end;

        this.addChangedLine(this.currentLine);
    }

    addChangedLine(changedLine) {
        addUniqueSortedInt(this.changedLines, changedLine, 0, this.changedLines.length);
    }

    getLine(lineIndex) {
        let length = this.lines.length;
        while (length <= lineIndex) {
            this.lines.push('');
            length++;
        }

        return this.lines[lineIndex];
    }

    setStyle(style) {
        if (style.isEmpty()) {
            this.currentStyle = null;
        } else {
            this.currentStyle = style;
        }
    }

    setCursorPosition(line, row) {
        this.currentLine = line;
        this.currentPosition = row;
    }

    handleCommand(args, commandCharacter) {
        const handler = COMMAND_HANDLERS.get(commandCharacter);
        if (handler === null) {
            return;
        }

        if (!handler.isValidArgumentsCount(args.length)) {
            return;
        }

        handler.handle(args, this);
    }

    updateTextStyle(lineIndex, start, end, style) {
        const emptyStyle = (style === null) || (style.isEmpty());

        if (!this.lineStyles.has(lineIndex)) {
            if (!emptyStyle) {
                this.lineStyles.set(lineIndex, [new StyledRange(start, end, style)]);
            }
            return;
        }

        const styles = this.lineStyles.get(lineIndex);

        let index = 0;
        while ((index < styles.length) && (styles[index].end <= start)) {
            index++;
        }

        if (index >= styles.length) {
            if (!emptyStyle) {
                styles.push(new StyledRange(start, end, style));
            }
            return;
        }

        const firstIntersection = styles[index];
        if (firstIntersection.start < start) {
            index++;

            if (firstIntersection.end > end) {
                styles.splice(index, 0, new StyledRange(start, end, style));
                styles.splice(index + 1, 0,
                    new StyledRange(end, firstIntersection.end, firstIntersection.style));
                firstIntersection.end = start;
                return;
            }

            firstIntersection.end = start;
        }

        styles.splice(index, 0, new StyledRange(start, end, style));
        index++;

        while (index < styles.length) {
            const existing = styles[index];
            if (existing.end <= end) {
                styles.splice(index, 1);
            } else if (existing.start >= end) {
                return;
            } else {
                existing.start = end;
                return;
            }
        }
    }
}

export class Style {
    constructor(params) {
        this.styles = [];

        if (!isNull(params)) {
            let {color, background, styles} = params;
            if (!isNull(color)) {
                this.color = color;
            }

            if (!isNull(background)) {
                this.background = background;
            }

            if (!isEmptyArray(styles)) {
                this.styles.push(...styles);
            }
        }
    }

    clone() {
        const style = new Style();
        style.color = this.color;
        style.background = this.background;
        style.styles = [...this.styles];
        return style;
    }

    isEmpty() {
        return isNull(this.color)
            && isNull(this.background)
            && isEmptyArray(this.styles)
    }

    equals(anotherStyle) {
        return (this.color === anotherStyle.color)
            && (this.background === anotherStyle.background)
            && (arraysEqual(this.styles, anotherStyle.styles));
    }
}

export class StyledRange {
    constructor(start, end, style) {
        this.start = start;
        this.end = end;
        this.style = style;
    }
}

function replaceAt(str, index, substr) {
    if (str.length < index) {
        return str + (' '.repeat(index - str.length)) + substr;
    }

    if (str.length === index) {
        return str + substr;
    }

    return str.substr(0, index) + substr + str.substr(index + substr.length);
}

function prepareArguments(argsStr) {
    const chunks = fastSplit(argsStr, ';');

    const preparedArguments = [];

    for (const arg of chunks) {
        if (arg === '') {
            preparedArguments.push(0);
            continue;
        }

        const intArg = parseInt(arg);
        if ((intArg < 0) || isNaN(intArg)) {
            continue;
        }

        preparedArguments.push(intArg);
    }

    return preparedArguments;
}

// for some reason default split (on chrome) is slower in 3-4 times
function fastSplit(str, separatorChar) {
    if (str === '') {
        return [''];
    }

    let result = [];

    let lastIndex = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str[i];
        if (char === separatorChar) {
            const chunk = str.substr(lastIndex, i - lastIndex);
            lastIndex = i + 1;
            result.push(chunk);
        }
    }

    if (lastIndex < str.length) {
        const lastChunk = str.substr(lastIndex, str.length - lastIndex);
        result.push(lastChunk);
    }

    return result;
}

class CommandHandler {
    constructor(minArgumentsCount = 1, maxArgumentsCount = 1) {
        this.minArgumentsCount = minArgumentsCount;
        this.maxArgumentsCount = maxArgumentsCount;
    }

    isValidArgumentsCount(count) {
        return this.minArgumentsCount <= count <= this.maxArgumentsCount;
    }
}

class SetGraphicsCommandHandler extends CommandHandler {
    constructor() {
        super(1, 10);
    }

    handle(args, terminal) {
        const resetGraphics = contains(args, 0);

        let style = (resetGraphics || terminal.currentStyle == null) ? new Style() : terminal.currentStyle.clone();
        for (let arg of args) {
            if (TEXT_COLOR_DICT.has(arg)) {
                style.color = TEXT_COLOR_DICT.get(arg);
            } else if (BACKGROUND_COLOR_DICT.has(arg)) {
                style.background = BACKGROUND_COLOR_DICT.get(arg);
            } else if (TEXT_STYLES_DICT.has(arg)) {
                style.styles.push(TEXT_STYLES_DICT.get(arg));
            } else if (RESET_STYLES_DICT.has(arg)) {
                removeElement(style.styles, RESET_STYLES_DICT.get(arg));
            }
        }

        terminal.setStyle(style);
    }
}


class MoveCursorVerticallyHandler extends CommandHandler {
    constructor(moveUp) {
        super();

        this.moveUp = moveUp;
    }

    handle(args, terminal) {
        const delta = args[0];

        let newLine;
        if (this.moveUp) {
            newLine = Math.max(0, terminal.currentLine - delta);
        } else {
            newLine = Math.min(terminal.currentLine + delta, terminal.maxLine);
        }
        terminal.setCursorPosition(newLine, terminal.currentPosition);
    }
}

class MoveCursorHorizontallyHandler extends CommandHandler {
    constructor(moveRight) {
        super();

        this.moveRight = moveRight;
    }

    handle(args, terminal) {
        const delta = args[0];

        let newPosition;
        if (this.moveRight) {
            newPosition = terminal.currentPosition + delta;
        } else {
            newPosition = Math.max(0, terminal.currentPosition - delta);
        }
        terminal.setCursorPosition(terminal.currentLine, newPosition);
    }
}

class MoveCursorToPositionHandler extends CommandHandler {
    constructor() {
        super(1, 2);
    }

    handle(args, terminal) {
        const line = Math.min(args[0], terminal.maxLine);
        let position;

        if (args.length === 1) {
            position = 0;
        } else {
            position = args[1];
        }

        if ((position < 0) || (line < 0)) {
            console.log('Negative line/column are not allowed: were ' + line + ';' + position);
            return;
        }

        terminal.setCursorPosition(line, position);
    }
}

class SaveCursorPositionHandler extends CommandHandler {
    handle(args, terminal) {
        terminal.savedCursorPosition = [terminal.currentLine, terminal.currentPosition];
    }
}

class RestoreCursorPositionHandler extends CommandHandler {
    handle(args, terminal) {
        if (isNull(terminal.savedCursorPosition)) {
            console.log('WARN! trying to restore cursor position, but nothing is saved');
            return;
        }
        const [line, position] = terminal.savedCursorPosition;
        terminal.setCursorPosition(line, position);
    }
}

class ClearLineHandler extends CommandHandler {
    constructor() {
        super();
    }

    handle(args, terminal) {
        const direction = args[0];

        if (direction === 0) {
            terminal.clearLineToRight();
        } else if (direction === 1) {
            terminal.clearLineToLeft();
        } else if (direction === 2) {
            terminal.clearFullLine();
        } else {
            console.log('WARN! Unsupported [' + direction + 'K command');
        }
    }
}

const COMMAND_HANDLERS = new Map();
COMMAND_HANDLERS.set('m', new SetGraphicsCommandHandler());
COMMAND_HANDLERS.set('K', new ClearLineHandler());
COMMAND_HANDLERS.set('J', null);
COMMAND_HANDLERS.set('H', new MoveCursorToPositionHandler());
COMMAND_HANDLERS.set('f', new MoveCursorToPositionHandler());
COMMAND_HANDLERS.set('A', new MoveCursorVerticallyHandler(true));
COMMAND_HANDLERS.set('B', new MoveCursorVerticallyHandler(false));
COMMAND_HANDLERS.set('C', new MoveCursorHorizontallyHandler(true));
COMMAND_HANDLERS.set('D', new MoveCursorHorizontallyHandler(false));
COMMAND_HANDLERS.set('s', new SaveCursorPositionHandler());
COMMAND_HANDLERS.set('u', new RestoreCursorPositionHandler());

const TEXT_COLOR_DICT = new Map();
TEXT_COLOR_DICT.set(39, null);
TEXT_COLOR_DICT.set(31, 'red');
TEXT_COLOR_DICT.set(30, 'black');
TEXT_COLOR_DICT.set(32, 'green');
TEXT_COLOR_DICT.set(33, 'yellow');
TEXT_COLOR_DICT.set(34, 'blue');
TEXT_COLOR_DICT.set(35, 'magenta');
TEXT_COLOR_DICT.set(36, 'cyan');
TEXT_COLOR_DICT.set(37, 'lightgray');
TEXT_COLOR_DICT.set(90, 'darkgray');
TEXT_COLOR_DICT.set(91, 'lightred');
TEXT_COLOR_DICT.set(92, 'lightgreen');
TEXT_COLOR_DICT.set(93, 'lightyellow');
TEXT_COLOR_DICT.set(94, 'lightblue');
TEXT_COLOR_DICT.set(95, 'lightmagenta');
TEXT_COLOR_DICT.set(96, 'lightcyan');
TEXT_COLOR_DICT.set(97, 'white');

const BACKGROUND_COLOR_DICT = new Map();
BACKGROUND_COLOR_DICT.set(49, null);
BACKGROUND_COLOR_DICT.set(41, 'red');
BACKGROUND_COLOR_DICT.set(40, 'black');
BACKGROUND_COLOR_DICT.set(42, 'green');
BACKGROUND_COLOR_DICT.set(43, 'yellow');
BACKGROUND_COLOR_DICT.set(44, 'blue');
BACKGROUND_COLOR_DICT.set(45, 'magenta');
BACKGROUND_COLOR_DICT.set(46, 'cyan');
BACKGROUND_COLOR_DICT.set(47, 'lightgray');
BACKGROUND_COLOR_DICT.set(100, 'darkgray');
BACKGROUND_COLOR_DICT.set(101, 'lightred');
BACKGROUND_COLOR_DICT.set(102, 'lightgreen');
BACKGROUND_COLOR_DICT.set(103, 'lightyellow');
BACKGROUND_COLOR_DICT.set(104, 'lightblue');
BACKGROUND_COLOR_DICT.set(105, 'lightmagenta');
BACKGROUND_COLOR_DICT.set(106, 'lightcyan');
BACKGROUND_COLOR_DICT.set(107, 'white');

const TEXT_STYLES_DICT = new Map();
TEXT_STYLES_DICT.set(1, 'bold');
TEXT_STYLES_DICT.set(2, 'dim');
TEXT_STYLES_DICT.set(4, 'underlined');
TEXT_STYLES_DICT.set(8, 'hidden');

const RESET_STYLES_DICT = new Map();
RESET_STYLES_DICT.set(21, 'bold');
RESET_STYLES_DICT.set(22, 'dim');
RESET_STYLES_DICT.set(24, 'underlined');
RESET_STYLES_DICT.set(28, 'hidden');

const FORMAT_ESCAPE_CHARACTER = '\u001B';