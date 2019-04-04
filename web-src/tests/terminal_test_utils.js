const escapePrefix = '\u001B[';

export function format(...styles) {
    if (!Array.isArray(styles)) {
        styles = [styles];
    }

    return escapePrefix + styles.join(';') + 'm';
}

export function moveCursorUp(lines) {
    return escapePrefix + lines + 'A';
}

export function moveCursorDown(lines) {
    return escapePrefix + lines + 'B';
}

export function moveCursorLeft(positions) {
    return escapePrefix + positions + 'D';
}

export function moveCursorRight(positions) {
    return escapePrefix + positions + 'C';
}

export function clearLineToRight() {
    return clearLine('');
}

export function clearLineToLeft() {
    return clearLine('1');
}

export function clearFullLine() {
    return clearLine('2');
}

export function clearLine(arg) {
    return escapePrefix + arg + 'K';
}
