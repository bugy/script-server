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

export function moveCursorLeft(lines) {
    return escapePrefix + lines + 'D';
}

export function moveCursorRight(lines) {
    return escapePrefix + lines + 'C';
}