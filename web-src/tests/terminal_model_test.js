'use strict';

import {assert, config as chaiConfig, expect} from 'chai';
import * as sinon from 'sinon';
import {clearArray, isNull} from '../js/common';
import {Style, StyledRange, TerminalModel} from '../js/components/terminal/terminal_model';
import {
    clearFullLine,
    clearLine,
    clearLineToLeft,
    clearLineToRight,
    clearScreen,
    clearScreenDown,
    clearScreenUp,
    escapePrefix,
    format,
    moveCursorDown,
    moveCursorLeft,
    moveCursorRight,
    moveCursorUp,
    moveToPosition,
    restorePosition,
    savePosition
} from './terminal_test_utils';

chaiConfig.truncateThreshold = 0;

function addChangedLinesListener(testCase) {
    const changedLinesField = [];
    testCase.changedLines = changedLinesField;

    testCase.model.addListener({
        linesChanges: function (changedLines) {
            changedLinesField.push(changedLines);
        },

        cleared: function () {

        }
    });
}

describe('Test terminal model', function () {

    beforeEach(function () {
        this.model = new TerminalModel();
    });

    describe('Test simple writes', function () {

        it('Test write one char', function () {
            this.model.write('a');

            assert.deepEqual(['a'], this.model.lines);
        });

        it('Test write a string', function () {
            this.model.write('hello world');

            assert.deepEqual(['hello world'], this.model.lines);
        });

        it('Test write multiline string', function () {
            this.model.write('hello world\n1\nanother line');

            assert.deepEqual(['hello world', '1', 'another line'], this.model.lines);
        });

        it('Test multiple writes one char', function () {
            this.model.write('a');
            this.model.write('b');
            this.model.write('c');

            assert.deepEqual(['abc'], this.model.lines);
        });

        it('Test multiple writes string', function () {
            this.model.write('Lorem ');
            this.model.write('ipsum');
            this.model.write(' dolor');

            assert.deepEqual(['Lorem ipsum dolor'], this.model.lines);
        });

        it('Test multiple writes with newline', function () {
            this.model.write('sit\n');
            this.model.write('am\net, ');
            this.model.write('consectetur');

            assert.deepEqual(['sit', 'am', 'et, consectetur'], this.model.lines);
        });
    });

    function removeNullStyledRanges(styleRanges) {
        const result = [];

        for (const styleRange of styleRanges) {
            if (!isNull(styleRange.style)) {
                result.push(styleRange);
            }
        }

        return result;
    }

    function assertStyles(actual, expected) {
        function str(val) {
            return JSON.stringify(val, null, 2);
        }

        if (isNull(actual) && isNull(expected)) {
            return;
        }

        if (isNull(actual)) {
            assert.fail('Actual style is empty, but expected\n' + str(expected));
        }

        if (isNull(expected)) {
            assert.fail('Expected empty style but was\n' + str(actual));
        }

        const normalizedActual = removeNullStyledRanges(actual);
        const normalizedExpected = removeNullStyledRanges(expected);

        assert.equal(normalizedActual.length, normalizedExpected.length,
            'Different styles length. Expected:\n' + str(normalizedExpected) + '\n\nActual:\n' + str(normalizedActual));

        for (let i = 0; i < normalizedActual.length; i++) {
            const actualRange = normalizedActual[i];
            const expectedRange = normalizedExpected[i];

            const suffix = ` at index ${i}. Expected:\n${str(expectedRange)}\n\nActual:\n${str(actualRange)}`;
            assert.equal(actualRange.start, expectedRange.start, 'Different start' + suffix);
            assert.equal(actualRange.end, expectedRange.end, 'Different end' + suffix);

            const actualStyle = actualRange.style;
            const expectedStyle = expectedRange.style;

            if (isNull(actualStyle) !== isNull(expectedStyle)) {
                assert.fail('Undefined style' + suffix);
            }
            if (isNull(actualStyle)) {
                continue;
            }

            assert.equal(actualStyle.color, expectedStyle.color, 'Different color' + suffix);
            assert.equal(actualStyle.background, expectedStyle.background, 'Different background' + suffix);
            assert.deepEqual(actualStyle.styles, expectedStyle.styles, 'Different text styles' + suffix);
        }
    }

    describe('Test styles', function () {

        it('Test text without styles', function () {
            this.model.write('Lorem');

            assert.deepEqual(['Lorem'], this.model.lines);
            assert(isNull(this.model.getStyle(0)));
        });

        it('Test colored text', function () {
            this.model.write(format(31) + 'ipsum');

            assert.deepEqual(['ipsum'], this.model.lines);
            assertStyles(this.model.getStyle(0), [new StyledRange(0, 5, new Style({color: 'red'}))]);
        });

        it('Test text style', function () {
            this.model.write(format(1) + 'ipsum');

            assert.deepEqual(['ipsum'], this.model.lines);
            assertStyles(this.model.getStyle(0), [new StyledRange(0, 5, new Style({styles: ['bold']}))]);
        });

        it('Test text style zero-padded', function () {
            this.model.write(format('02') + 'ipsum');

            assert.deepEqual(['ipsum'], this.model.lines);
            assertStyles(this.model.getStyle(0), [new StyledRange(0, 5, new Style({styles: ['dim']}))]);
        });

        it('Test mixed colored text', function () {
            this.model.write(format(31) + '12345 ' + format(0) + '678 ' + format(32) + '90ab');

            assert.deepEqual(['12345 678 90ab'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 6, new Style({color: 'red'})),
                new StyledRange(10, 14, new Style({color: 'green'}))]);
        });

        it('Test mixed colored text with new lines', function () {
            this.model.write(
                format(33) + '123 ' + format(34) + '45\n'
                + ' 6789 ' + format(31) + '0ab' + format(0) + ' ' + format(35) + 'cdefgh ijklmn' + format(0) + ' \n'
                + 'op\n'
                + format(36) + 'qrstuv');

            assert.deepEqual(['123 45', ' 6789 0ab cdefgh ijklmn ', 'op', 'qrstuv'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 4, new Style({color: 'yellow'})),
                new StyledRange(4, 6, new Style({color: 'blue'}))]);
            assertStyles(this.model.getStyle(1), [
                new StyledRange(0, 6, new Style({color: 'blue'})),
                new StyledRange(6, 9, new Style({color: 'red'})),
                new StyledRange(10, 23, new Style({color: 'magenta'}))]);

            assert(isNull(this.model.getStyle(2)));

            assertStyles(this.model.getStyle(3), [
                new StyledRange(0, 6, new Style({color: 'cyan'}))]);
        });

        it('Test color + background + styles', function () {
            this.model.write(format(37, 41, 1, 4) + '12345');

            assert.deepEqual(['12345'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 5, new Style({
                    color: 'lightgray',
                    background: 'red',
                    styles: ['bold', 'underlined']
                }))]);
        });

        it('Test change color', function () {
            this.model.write(format(31, 41) + '123'
                + format(32) + '4'
                + format(39) + '567'
                + format(33) + '890abc');

            assert.deepEqual(['1234567890abc'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 3, new Style({color: 'red', background: 'red'})),
                new StyledRange(3, 4, new Style({color: 'green', background: 'red'})),
                new StyledRange(4, 7, new Style({background: 'red'})),
                new StyledRange(7, 13, new Style({color: 'yellow', background: 'red'}))]);
        });

        it('Test change styles', function () {
            this.model.write(
                format(34) + '123'
                + format(1) + '45'
                + format(4) + '67890'
                + format(21) + 'a'
                + format(24) + 'bcd'
                + format(1, 2) + 'e'
                + format(21, 22) + 'f'
                + format(0) + 'ghi'
                + format(8) + 'jkl'
                + format(28) + 'mno'
                + format(2) + 'pq');

            assert.deepEqual(['1234567890abcdefghijklmnopq'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 3, new Style({color: 'blue'})),
                new StyledRange(3, 5, new Style({color: 'blue', styles: ['bold']})),
                new StyledRange(5, 10, new Style({color: 'blue', styles: ['bold', 'underlined']})),
                new StyledRange(10, 11, new Style({color: 'blue', styles: ['underlined']})),
                new StyledRange(11, 14, new Style({color: 'blue'})),
                new StyledRange(14, 15, new Style({color: 'blue', styles: ['bold', 'dim']})),
                new StyledRange(15, 16, new Style({color: 'blue'})),
                new StyledRange(19, 22, new Style({styles: ['hidden']})),
                new StyledRange(25, 27, new Style({styles: ['dim']}))]);
        });

        it('Test replace style on ', function () {
            this.model.write(
                format(34) + '123'
                + format(1) + '45'
                + format(4) + '67890'
                + format(21) + 'a'
                + format(24) + 'bcd'
                + format(1, 2) + 'e'
                + format(21, 22) + 'f'
                + format(0) + 'ghi'
                + format(8) + 'jkl'
                + format(28) + 'mno'
                + format(2) + 'pq');

            assert.deepEqual(['1234567890abcdefghijklmnopq'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 3, new Style({color: 'blue'})),
                new StyledRange(3, 5, new Style({color: 'blue', styles: ['bold']})),
                new StyledRange(5, 10, new Style({color: 'blue', styles: ['bold', 'underlined']})),
                new StyledRange(10, 11, new Style({color: 'blue', styles: ['underlined']})),
                new StyledRange(11, 14, new Style({color: 'blue'})),
                new StyledRange(14, 15, new Style({color: 'blue', styles: ['bold', 'dim']})),
                new StyledRange(15, 16, new Style({color: 'blue'})),
                new StyledRange(19, 22, new Style({styles: ['hidden']})),
                new StyledRange(25, 27, new Style({styles: ['dim']}))]);
        });

        it('Test fully replace styled line with another styled line', function () {
            this.model.write(format(31) + '12345' + format(32) + '\r67890');

            assert.deepEqual(['67890'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 5, new Style({color: 'green'}))]);
        });

        it('Test fully replace unstyled line with a styled line', function () {
            this.model.write('12345' + format(32) + '\r67890');

            assert.deepEqual(['67890'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 5, new Style({color: 'green'}))]);
        });

        it('Test fully replace styled line with an unstyled line', function () {
            this.model.write(format(31) + '12345' + format(0) + '\r67890');

            assert.deepEqual(['67890'], this.model.lines);
            assertStyles(this.model.getStyle(0), []);
        });

        it('Test replace beginning of styled line', function () {
            this.model.write(format(31) + '12345' + format(0, 42) + '\rabc');

            assert.deepEqual(['abc45'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 3, new Style({background: 'green'})),
                new StyledRange(3, 5, new Style({color: 'red'}))]);
        });

        it('Test replace mid of styled line', function () {
            this.model.write(format(31) + '12345' + format(0, 42) + moveCursorLeft(4) + 'abc');

            assert.deepEqual(['1abc5'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 1, new Style({color: 'red'})),
                new StyledRange(1, 4, new Style({background: 'green'})),
                new StyledRange(4, 5, new Style({color: 'red'}))]);
        });

        it('Test replace end of styled line', function () {
            this.model.write(format(31) + '12345' + format(0, 42) + moveCursorLeft(2) + 'abc');

            assert.deepEqual(['123abc'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 3, new Style({color: 'red'})),
                new StyledRange(3, 6, new Style({background: 'green'}))]);
        });

        it('Test replace multiple styles', function () {
            this.model.write('123' + format(31) + '456' + format(42) + '78' + format(2) + '90'
                + format(0, 33) + '\r' + 'abcdefghi');

            assert.deepEqual(['abcdefghi0'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 9, new Style({color: 'yellow'})),
                new StyledRange(9, 10, new Style({color: 'red', background: 'green', styles: ['dim']}))]);
        });

        it('Test replace multiple styles without format', function () {
            this.model.write(format(31) + '123' + format(2) + '456' + format(42) + '78' + format(0, 33) + '90'
                + format(0) + '\r' + moveCursorRight(1) + 'abcdefgh');

            assert.deepEqual(['1abcdefgh0'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 1, new Style({color: 'red'})),
                new StyledRange(9, 10, new Style({color: 'yellow'}))]);
        });

        it('Test replace multiple styles with intervals', function () {
            this.model.write(
                format(31) + 'abcd' + format(2) + 'efg' + format(44) + 'h' + format(0) + 'ij' + format(33) + 'klmno'
                + format(0, 32) + '\r' + moveCursorRight(1) + '1' + moveCursorRight(5) + '23' + moveCursorRight(2) + '45');

            assert.deepEqual(['a1cdefg23jk45no'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 1, new Style({color: 'red'})),
                new StyledRange(1, 2, new Style({color: 'green'})),
                new StyledRange(2, 4, new Style({color: 'red'})),
                new StyledRange(4, 7, new Style({color: 'red', styles: ['dim']})),
                new StyledRange(7, 9, new Style({color: 'green'})),
                new StyledRange(10, 11, new Style({color: 'yellow'})),
                new StyledRange(11, 13, new Style({color: 'green'})),
                new StyledRange(13, 15, new Style({color: 'yellow'}))]);
        });

    });

    describe('Test changed lines', function () {

        beforeEach(function () {
            addChangedLinesListener(this);
        });

        it('Test write one char', function () {
            this.model.write('a');

            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test text with newline', function () {
            this.model.write('hello world\n');

            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test write multiline string', function () {
            this.model.write('hello world\n1\nanother line');

            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test multiple writes', function () {
            this.model.write('12');
            this.model.write('3');

            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test write after multiline', function () {
            this.model.write('hello\n');
            this.model.write('world');

            assert.deepEqual([[0], [1]], this.changedLines);
        });

        it('Test write with first char newline', function () {
            this.model.write('hello');
            this.model.write('\nworld');

            assert.deepEqual([[0], [1]], this.changedLines);
        });

        it('Test multiple newlines', function () {
            this.model.write('123\n\n\n456');

            assert.deepEqual([[0, 3]], this.changedLines);
        });

        it('Test multiple writes with newline', function () {
            this.model.write('123\n');
            this.model.write('45\n678');
            this.model.write('9\n10\n11');

            assert.deepEqual([[0], [1, 2], [2, 3, 4]], this.changedLines);
        });
    });

    describe('Test cursor move', function () {

        it('Test caret return without changes', function () {
            this.model.write('12345\r');

            assert.deepEqual(['12345'], this.model.lines);
        });

        it('Test caret return and char change', function () {
            this.model.write('12345\ra');

            assert.deepEqual(['a2345'], this.model.lines);
        });

        it('Test caret return and long change', function () {
            this.model.write('12345\rabcdef');

            assert.deepEqual(['abcdef'], this.model.lines);
        });

        it('Test caret return and newline', function () {
            this.model.write('12345\r\nabcdef');

            assert.deepEqual(['12345', 'abcdef'], this.model.lines);
        });

        it('Test caret return and newline after a char', function () {
            this.model.write('12345\ra\nbcdef');

            assert.deepEqual(['a2345', 'bcdef'], this.model.lines);
        });

        it('Test caret return in multiple lines', function () {
            this.model.write('12345\ra\nb\n\rcdef');

            assert.deepEqual(['a2345', 'b', 'cdef'], this.model.lines);
        });

        it('Test move cursor up when one line only', function () {
            this.model.write('12345' + moveCursorUp(1) + 'abc');

            assert.deepEqual(['12345abc'], this.model.lines);
        });

        it('Test move cursor up from the second line', function () {
            this.model.write('12345\nabc' + moveCursorUp(1) + 'def');

            assert.deepEqual(['123def', 'abc'], this.model.lines);
        });

        it('Test move cursor up when upper line is shorter', function () {
            this.model.write('1\nabc' + moveCursorUp(1) + 'def');

            assert.deepEqual(['1  def', 'abc'], this.model.lines);
        });

        it('Test move cursor up above terminal', function () {
            this.model.write('123\n456\n78' + moveCursorUp(100) + 'def');

            assert.deepEqual(['12def', '456', '78'], this.model.lines);
        });

        it('Test move cursor up, when 2 writes and second write moves up to itself', function () {
            this.model.write('12345\n');
            this.model.write('abc\nde' + moveCursorUp(1) + 'fgh');

            assert.deepEqual(['12345', 'abfgh', 'de'], this.model.lines);
        });

        it('Test move cursor up, when 2 writes and second write moves up 1 line to previous write', function () {
            this.model.write('12345\n');
            this.model.write('abc' + moveCursorUp(1) + 'def');

            assert.deepEqual(['123def', 'abc'], this.model.lines);
        });

        it('Test move cursor up, when 2 writes and second write moves up 2 lines to previous write', function () {
            this.model.write('12345\n');
            this.model.write('abc\nde' + moveCursorUp(2) + 'fgh');

            assert.deepEqual(['12fgh', 'abc', 'de'], this.model.lines);
        });

        it('Test move cursor down to unexisting line', function () {
            this.model.write('1' + moveCursorDown(1) + 'abc');

            assert.deepEqual(['1abc'], this.model.lines);
        });

        it('Test move cursor down N to unexisting line', function () {
            this.model.write('12345' + moveCursorDown(3) + 'a');

            assert.deepEqual(['12345a'], this.model.lines);
        });

        it('Test move cursor down to empty line', function () {
            this.model.write('1\n' + moveCursorUp(1) + moveCursorDown(1) + 'abc');

            assert.deepEqual(['1', 'abc'], this.model.lines);
        });

        it('Test move cursor down 3 times, when only 2 empty lines', function () {
            this.model.write('1\n\n' + moveCursorUp(2) + moveCursorDown(3) + 'abc');

            assert.deepEqual(['1', '', 'abc'], this.model.lines);
        });

        it('Test move cursor down N to unexisting line', function () {
            this.model.write('12345' + moveCursorDown(3) + 'a');

            assert.deepEqual(['12345a'], this.model.lines);
        });

        it('Test move cursor down when bottom line is shorter', function () {
            this.model.write('12\n34\n56' + moveCursorUp(3) + '\rabcdef' + moveCursorDown(2) + 'gh');

            assert.deepEqual(['abcdef', '34', '56    gh'], this.model.lines);
        });

        it('Test move cursor down when bottom line is longer', function () {
            this.model.write('12\n3456789\n' + moveCursorUp(2) + '\ra' + moveCursorDown(1) + 'bc');

            assert.deepEqual(['a2', '3bc6789'], this.model.lines);
        });

        it('Test move cursor down N to existing line', function () {
            this.model.write('12\n34\n56\n78\n' + moveCursorUp(4) + 'a' + moveCursorDown(3) + 'b');

            assert.deepEqual(['a2', '34', '56', '7b'], this.model.lines);
        });

        it('Test move cursor down multiple times', function () {
            this.model.write('12\n34\n56\n78\n90\n' + moveCursorUp(5)
                + moveCursorDown(2) + moveCursorDown(1) + 'b');

            assert.deepEqual(['12', '34', '56', 'b8', '90'], this.model.lines);
        });

        it('Test move cursor right 1 position', function () {
            this.model.write('123' + moveCursorRight(1) + 'abc');

            assert.deepEqual(['123 abc'], this.model.lines);
        });

        it('Test move cursor right N positions', function () {
            this.model.write('123' + moveCursorRight(5) + 'abc');

            assert.deepEqual(['123     abc'], this.model.lines);
        });

        it('Test move cursor right when existing text is shorter', function () {
            this.model.write('123\r' + moveCursorRight(5) + 'abc');

            assert.deepEqual(['123  abc'], this.model.lines);
        });

        it('Test move cursor right when existing text is longer', function () {
            this.model.write('1234567890\r' + moveCursorRight(5) + 'abc');

            assert.deepEqual(['12345abc90'], this.model.lines);
        });

        it('Test move cursor right multiple times', function () {
            this.model.write('1234567890\r' + moveCursorRight(3) + moveCursorRight(1) + moveCursorRight(2) + 'abc');

            assert.deepEqual(['123456abc0'], this.model.lines);
        });

        it('Test move cursor left 1 position and single char', function () {
            this.model.write('12345' + moveCursorLeft(1) + 'a');

            assert.deepEqual(['1234a'], this.model.lines);
        });

        it('Test move cursor left 1 position and long string', function () {
            this.model.write('12345' + moveCursorLeft(1) + 'abcde');

            assert.deepEqual(['1234abcde'], this.model.lines);
        });

        it('Test move cursor left N positions ', function () {
            this.model.write('12345' + moveCursorLeft(4) + 'abc');

            assert.deepEqual(['1abc5'], this.model.lines);
        });

        it('Test move cursor left out of terminal', function () {
            this.model.write('12345' + moveCursorLeft(100) + 'abc');

            assert.deepEqual(['abc45'], this.model.lines);
        });

        it('Test move cursor right left has no effect', function () {
            this.model.write('12345' + moveCursorRight(5) + moveCursorLeft(5) + 'abc');

            assert.deepEqual(['12345abc'], this.model.lines);
        });

        it('Test move cursor left right has no effect', function () {
            this.model.write('12345' + moveCursorLeft(3) + moveCursorRight(3) + 'abc');

            assert.deepEqual(['12345abc'], this.model.lines);
        });

        it('Test move cursor down up has no effect', function () {
            this.model.write('12345' + moveCursorDown(5) + moveCursorUp(5) + 'abc');

            assert.deepEqual(['12345abc'], this.model.lines);
        });

        it('Test move cursor up down has no effect', function () {
            this.model.write('12\n34\n56\n78\n90' + moveCursorUp(3) + moveCursorDown(3) + 'abc');

            assert.deepEqual(['12', '34', '56', '78', '90abc'], this.model.lines);
        });
    });

    describe('Test clear line command', function () {
        beforeEach(function () {
            addChangedLinesListener(this);

            sinon.stub(console, 'log').returns(void 0);
        });

        afterEach(function () {
            console.log.restore();
        });

        it('Test clear line to the right in the middle, same write', function () {
            this.model.write('123456' + moveCursorLeft(3) + clearLineToRight());

            assert.deepEqual(['123'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the right at the beginning, same write', function () {
            this.model.write('123456' + moveCursorLeft(6) + clearLineToRight());

            assert.deepEqual([''], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the right in the middle, second write', function () {
            this.model.write('123456' + moveCursorLeft(3));
            this.model.write(clearLineToRight());

            assert.deepEqual(['123'], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the right before last, second write', function () {
            this.model.write('123456' + moveCursorLeft(1));
            this.model.write(clearLineToRight());

            assert.deepEqual(['12345'], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the right after last, second write', function () {
            this.model.write('123456');
            this.model.write(clearLineToRight());

            assert.deepEqual(['123456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the right one position after last, second write', function () {
            this.model.write('123456' + moveCursorRight(1));
            this.model.write(clearLineToRight());

            assert.deepEqual(['123456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the right many positions after last, second write', function () {
            this.model.write('123456' + moveCursorRight(5));
            this.model.write(clearLineToRight());

            assert.deepEqual(['123456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the right, one line above, second write', function () {
            this.model.write('123456\nabc' + moveCursorUp(1));
            this.model.write(clearLineToRight());

            assert.deepEqual(['123', 'abc'], this.model.lines);
            assert.deepEqual([[0, 1], [0]], this.changedLines);
        });

        it('Test clear line to the left in the middle, same write', function () {
            this.model.write('123456' + moveCursorLeft(3) + clearLineToLeft());

            assert.deepEqual(['   456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the left in the middle, second write', function () {
            this.model.write('123456' + moveCursorLeft(3));
            this.model.write(clearLineToLeft());

            assert.deepEqual(['   456'], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the left before last, second write', function () {
            this.model.write('123456' + moveCursorLeft(1));
            this.model.write(clearLineToLeft());

            assert.deepEqual(['     6'], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the left after last, second write', function () {
            this.model.write('123456');
            this.model.write(clearLineToLeft());

            assert.deepEqual([''], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the left one position after last, second write', function () {
            this.model.write('123456' + moveCursorRight(1));
            this.model.write(clearLineToLeft());

            assert.deepEqual([''], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the left at position 1, second write', function () {
            this.model.write('123456' + moveCursorLeft(5));
            this.model.write(clearLineToLeft());

            assert.deepEqual([' 23456'], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear line to the left at position 0, second write', function () {
            this.model.write('123456' + moveCursorLeft(6));
            this.model.write(clearLineToLeft());

            assert.deepEqual(['123456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear line to the left, one line above, second write', function () {
            this.model.write('123456\nabc' + moveCursorUp(1));
            this.model.write(clearLineToLeft());

            assert.deepEqual(['   456', 'abc'], this.model.lines);
            assert.deepEqual([[0, 1], [0]], this.changedLines);
        });

        it('Test clear full in the middle, same write', function () {
            this.model.write('123456' + moveCursorLeft(3) + clearFullLine());

            assert.deepEqual([''], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test clear full in the middle, second write', function () {
            this.model.write('123456' + moveCursorLeft(3));
            this.model.write(clearFullLine());

            assert.deepEqual([''], this.model.lines);
            assert.deepEqual([[0], [0]], this.changedLines);
        });

        it('Test clear full line, one line above, second write', function () {
            this.model.write('123456\nabc' + moveCursorUp(1));
            this.model.write(clearFullLine());

            assert.deepEqual(['', 'abc'], this.model.lines);
            assert.deepEqual([[0, 1], [0]], this.changedLines);
        });

        it('Test clear line wrong parameter', function () {
            this.model.write('123456' + moveCursorLeft(3) + clearLine(3));

            assert.deepEqual(['123456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
            expect(console.log.args[0][0]).to.equal('WARN! Unsupported [3K command');
        });
    });

    describe('Test move cursor to position', function () {
        beforeEach(function () {
            addChangedLinesListener(this);
        });

        it('Test move to middle in the first line', function () {
            this.model.write('123456' + moveToPosition(0, 3) + 'abc');

            assert.deepEqual(['123abc'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move to explicit beginning in the first line', function () {
            this.model.write('123456' + moveToPosition(0, 0) + 'abc');

            assert.deepEqual(['abc456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move to the end in the first line', function () {
            this.model.write('123456' + moveToPosition(0, 6) + 'abc');

            assert.deepEqual(['123456abc'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move after the end in the first line', function () {
            this.model.write('123456' + moveToPosition(0, 7) + 'abc');

            assert.deepEqual(['123456 abc'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move after the end in the second line, when 3 lines', function () {
            this.model.write('12\n3456\n789' + moveToPosition(1, 7) + 'abc');

            assert.deepEqual(['12', '3456   abc', '789'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test move to the second line from the end, when 3 lines available', function () {
            this.model.write('1234\n5678\n90' + moveToPosition(1, 3) + 'abc');

            assert.deepEqual(['1234', '567abc', '90'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test move to the first line from the end, when 3 lines available', function () {
            this.model.write('1234\n5678\n90' + moveToPosition(0, 2) + 'abc');

            assert.deepEqual(['12abc', '5678', '90'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test move to the implicit beginning from the end, when 3 lines available', function () {
            this.model.write('1234\n5678\n90' + moveToPosition('', '') + 'abc');

            assert.deepEqual(['abc4', '5678', '90'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test move to the last line, when 3 lines available', function () {
            this.model.write('1234\n5678\n90' + moveCursorUp(2) + moveToPosition(2, 1) + 'abc');

            assert.deepEqual(['1234', '5678', '9abc'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test move to the second line, when only one is available', function () {
            this.model.write('123456' + moveToPosition(1, 0) + 'abc');

            assert.deepEqual(['abc456'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move to the third line, when only two are available', function () {
            this.model.write('12345\n67890' + moveCursorUp(1) + moveToPosition(2, 2) + 'abc');

            assert.deepEqual(['12345', '67abc'], this.model.lines);
            assert.deepEqual([[0, 1]], this.changedLines);
        });

        it('Test move to line without specified column, when 1 line', function () {
            this.model.write('12345' + moveToPosition(0, '') + 'abc');

            assert.deepEqual(['abc45'], this.model.lines);
            assert.deepEqual([[0]], this.changedLines);
        });

        it('Test move to the first line without specified column, when 2 lines', function () {
            this.model.write('12345\n67890' + moveToPosition(0, '') + 'abc');

            assert.deepEqual(['abc45', '67890'], this.model.lines);
            assert.deepEqual([[0, 1]], this.changedLines);
        });

        it('Test move to the second line without specified column, when 2 lines', function () {
            this.model.write('12345\n67890' + moveToPosition(1, '') + 'abc');

            assert.deepEqual(['12345', 'abc90'], this.model.lines);
            assert.deepEqual([[0, 1]], this.changedLines);
        });

        it('Test f command', function () {
            this.model.write('1234\n56\n7890' + moveToPosition(1, 1, 'f') + 'abc');

            assert.deepEqual(['1234', '5abc', '7890'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test without any arguments', function () {
            this.model.write('1234\n56\n7890' + escapePrefix + 'H' + 'abc');

            assert.deepEqual(['abc4', '56', '7890'], this.model.lines);
            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test changed lines, when no text', function () {
            this.model.write('1234\n56');
            this.model.write(moveToPosition(0, 0));

            assert.deepEqual(['1234', '56'], this.model.lines);
            assert.deepEqual([[0, 1]], this.changedLines);
        });

        it('Test changed lines, when text in the first line', function () {
            this.model.write('1234\n56\n789');
            this.model.write(moveToPosition(0, 1) + 'abc');

            assert.deepEqual(['1abc', '56', '789'], this.model.lines);
            assert.deepEqual([[0, 1, 2], [0]], this.changedLines);
        });

        it('Test changed lines, when text in the second line', function () {
            this.model.write('1234\n56\n789');
            this.model.write(moveToPosition(1, 1) + 'abc');

            assert.deepEqual(['1234', '5abc', '789'], this.model.lines);
            assert.deepEqual([[0, 1, 2], [1]], this.changedLines);
        });

        it('Test changed lines, when text in the last line', function () {
            this.model.write('1234\n56\n789');
            this.model.write(moveToPosition(2, 2) + 'abc');

            assert.deepEqual(['1234', '56', '78abc'], this.model.lines);
            assert.deepEqual([[0, 1, 2], [2]], this.changedLines);
        });
    });

    describe('Save/restore cursor position', function () {
        beforeEach(function () {
            sinon.stub(console, 'log').returns(void 0);
        });

        afterEach(function () {
            console.log.restore();
        });

        it('Test restore in the first line', function () {
            this.model.write('1234' + savePosition() + '5678' + restorePosition() + 'abc');

            assert.deepEqual(['1234abc8'], this.model.lines);
        });

        it('Test restore in the first line, when 3 lines', function () {
            this.model.write('123' + savePosition() + '45\n678\n90' + restorePosition() + 'abc');

            assert.deepEqual(['123abc', '678', '90'], this.model.lines);
        });

        it('Test restore in the last line, when 3 lines', function () {
            this.model.write('123\n4567\n8' + savePosition() + '90' + moveCursorUp(2) + 'X'
                + restorePosition() + 'abc');

            assert.deepEqual(['123X', '4567', '8abc'], this.model.lines);
        });

        it('Test restore position without save', function () {
            this.model.write('1234' + restorePosition() + 'abc');

            assert.deepEqual(['1234abc'], this.model.lines);
            expect(console.log.args[0][0]).to.equal('WARN! trying to restore cursor position, but nothing is saved');
        });

        it('Test restore position after clear', function () {
            this.model.write('1234' + savePosition());
            this.model.clear();
            this.model.write('abc' + restorePosition() + 'XYZ');

            assert.deepEqual(['abcXYZ'], this.model.lines);
            expect(console.log.args[0][0]).to.equal('WARN! trying to restore cursor position, but nothing is saved');
        });
    });

    describe('Clear screen command', function () {
        function changedLinesNotification(changedLines) {
            return {'linesChanged': changedLines};
        }

        function clearedNotification() {
            return {'cleared': true};
        }

        function linesDeletedNotification(start, end) {
            return {'linesDeleted': [start, end]};
        }

        beforeEach(function () {
            const notifications = [];
            this.notifications = notifications;

            this.model.addListener({
                linesChanges: function (changedLines) {
                    notifications.push(changedLinesNotification(changedLines))
                },

                cleared: function () {
                    notifications.push(clearedNotification())
                },

                linesDeleted: function (start, end) {
                    notifications.push(linesDeletedNotification(start, end))
                }
            });

            sinon.stub(console, 'log').returns(void 0);
        });

        afterEach(function () {
            console.log.restore();
        });

        it('Clear full screen for single line', function () {
            this.model.write('123' + clearScreen() + 'abc');

            assert.deepEqual(['abc'], this.model.lines);
            assert.deepEqual([clearedNotification(), changedLinesNotification([0])], this.notifications);
        });

        it('Clear full screen for multiline', function () {
            this.model.write('123\n456\n789' + clearScreen() + 'abc');

            assert.deepEqual(['abc'], this.model.lines);
            assert.deepEqual([clearedNotification(), changedLinesNotification([0])], this.notifications);
        });

        it('Clear screen to the bottom for multiline', function () {
            this.model.write('12\n3456\n7\n890' + moveToPosition(1, 1) + clearScreenDown() + 'abc');

            assert.deepEqual(['12', '3abc'], this.model.lines);
            assert.deepEqual([linesDeletedNotification(2, 4), changedLinesNotification([0, 1])], this.notifications);
        });

        it('Clear screen to the bottom for multiline, when separate writes', function () {
            this.model.write('12\n3456\n7\n890' + moveToPosition(1, 1));
            assert.deepEqual([changedLinesNotification([0, 1, 2, 3])], this.notifications);
            clearArray(this.notifications);

            this.model.write(clearScreenDown());
            assert.deepEqual([linesDeletedNotification(2, 4)], this.notifications);
            clearArray(this.notifications);

            this.model.write('abc');
            assert.deepEqual([changedLinesNotification([1])], this.notifications);

            assert.deepEqual(['12', '3abc'], this.model.lines);
        });

        it('Clear screen to the bottom, when single line', function () {
            this.model.write('12345' + moveCursorLeft(2) + clearScreenDown() + 'abc');

            assert.deepEqual(['123abc'], this.model.lines);
            assert.deepEqual([changedLinesNotification([0])], this.notifications);
        });

        it('Clear screen to the top', function () {
            this.model.write('12\n3456\n7\n890' + moveToPosition(1, 1) + clearScreenUp() + 'abc');

            assert.deepEqual([' abc', '7', '890'], this.model.lines);
            assert.deepEqual([
                clearedNotification(),
                changedLinesNotification([0, 1, 2])], this.notifications);
        });

        it('Clear screen to the top, when separate writes', function () {
            this.model.write('12\n3456\n');
            this.model.write('7\n890' + moveToPosition(1, 1));
            assert.deepEqual([changedLinesNotification([0, 1]), changedLinesNotification([2, 3])], this.notifications);
            clearArray(this.notifications);

            this.model.write(clearScreenUp());
            assert.deepEqual([
                clearedNotification(),
                changedLinesNotification([0, 1, 2])], this.notifications);
            clearArray(this.notifications);

            this.model.write('abc');

            assert.deepEqual([' abc', '7', '890'], this.model.lines);
            assert.deepEqual([changedLinesNotification([0])], this.notifications);
        });

        it('Clear screen to the top, when single line', function () {
            this.model.write('12345' + moveCursorLeft(2) + clearScreenUp() + 'X');

            assert.deepEqual(['   X5'], this.model.lines);
            assert.deepEqual([changedLinesNotification([0])], this.notifications);
        });

        it('Test styles, when clear all', function () {
            this.model.write(format(31) + '123\n' + format(32) + '45' + format(33, 41) + '\n678'
                + clearScreen() + format(1) + 'abc');

            assert.deepEqual(['abc'], this.model.lines);
            assertStyles(this.model.getStyle(0), [new StyledRange(0, 3, new Style({styles: ['bold']}))]);
        });

        it('Test styles, when clear to the bottom', function () {
            this.model.write(format(31) + '123\n' + format(32) + '45' + format(33, 44) + '678\n90\nX'
                + moveCursorUp(2) + clearScreenDown() + 'ab\n' + format(2) + 'c');

            assert.deepEqual(['123', '4ab78', 'c'], this.model.lines);
            assertStyles(this.model.getStyle(0), [new StyledRange(0, 3, new Style({color: 'red'}))]);
            assertStyles(this.model.getStyle(1), [
                new StyledRange(0, 1, new Style({color: 'green'})),
                new StyledRange(1, 3, new Style({color: 'yellow', 'background': 'blue'})),
                new StyledRange(3, 5, new Style({color: 'yellow', 'background': 'blue'}))
            ]);
            assertStyles(this.model.getStyle(2), [
                new StyledRange(0, 1, new Style({color: 'yellow', 'background': 'blue', styles: ['dim']}))]);
            assertStyles(this.model.getStyle(3), null);
        });

        it('Test styles, when clear to the top', function () {
            this.model.write(format(31) + '123\n'
                + format(32) + '45' + format(33, 44) + '678\n'
                + format(0, 35) + '90\n'
                + 'X'
                + moveCursorUp(2) + clearScreenUp()
                + 'ab\n'
                + format(36, 2) + 'c');

            assert.deepEqual([' ab78', 'c0', 'X'], this.model.lines);
            assertStyles(this.model.getStyle(0), [
                new StyledRange(0, 1, new Style({color: 'green'})),
                new StyledRange(1, 3, new Style({color: 'magenta'})),
                new StyledRange(3, 5, new Style({color: 'yellow', 'background': 'blue'}))
            ]);
            assertStyles(this.model.getStyle(1), [
                new StyledRange(0, 1, new Style({color: 'cyan', styles: ['dim']})),
                new StyledRange(1, 2, new Style({color: 'magenta'}))]);
            assertStyles(this.model.getStyle(2), [
                new StyledRange(0, 1, new Style({color: 'magenta'}))]);
        });

        it('Test move cursor down after clear to the bottom', function () {
            this.model.write('1234\n56\n789\n0' + moveToPosition(1, 1) + clearScreenDown()
                + moveCursorDown(1) + 'abc');

            assert.deepEqual(['1234', '5abc'], this.model.lines);
        });

        it('Test move cursor down after clear to the top', function () {
            this.model.write('1234\n56\n789\n0' + moveToPosition(2, 1) + clearScreenUp()
                + moveCursorDown(2) + 'abc');

            assert.deepEqual(['  9', '0abc'], this.model.lines);
        });

        it('Test clear with argument 3', function () {
            this.model.write('1234\n56\n789' + moveToPosition(1, 1) + escapePrefix + '3J' + 'abc');

            assert.deepEqual(['abc'], this.model.lines);
            assert.deepEqual([clearedNotification(), changedLinesNotification([0])], this.notifications);
        });

        it('Test clear with argument 4', function () {
            this.model.write('1234\n56\n789' + moveToPosition(1, 1) + escapePrefix + '4J' + 'abc');

            assert.deepEqual(['1234', '5abc', '789'], this.model.lines);
            assert.deepEqual([changedLinesNotification([0, 1, 2])], this.notifications);
            expect(console.log.args[0][0]).to.equal('WARN! Unsupported [4J command');
        });
    });

    describe('Test inline images', function () {

        it('Test set inline image, when not exists', function () {
            addChangedLinesListener(this);

            this.model.write('abc\ndef');
            this.model.setInlineImage('my-img.png', 'hello.jpg');

            assert.deepEqual({'my-img.png': 'hello.jpg'}, this.model.inlineImages);
            assert.deepEqual([[0, 1]], this.changedLines);
        });

        it('Test set inline image, when exists', function () {
            addChangedLinesListener(this);

            this.model.write('abc\n_ my-img.png _ \ndef');
            this.model.setInlineImage('my-img.png', 'hello.jpg');

            assert.deepEqual([[0, 1, 2], [1]], this.changedLines);
        });

        it('Test set inline image, when exists and multiple', function () {
            addChangedLinesListener(this);

            this.model.write('abc\n_ my-img.png _ \ndef\nmy-img.png\nhij\nmy-img.png');
            this.model.setInlineImage('my-img.png', 'hello.jpg');

            assert.deepEqual([[0, 1, 2, 3, 4, 5], [1, 3, 5]], this.changedLines);
        });

        it('Test remove inline image, when not exists', function () {
            addChangedLinesListener(this);

            this.model.write('abc\n_ my-img.png _ \ndef');
            this.model.removeInlineImage('my-img.png');

            assert.deepEqual([[0, 1, 2]], this.changedLines);
        });

        it('Test remove inline image, when exists', function () {
            addChangedLinesListener(this);

            this.model.setInlineImage('my-img.png', 'hello.jpg');
            this.model.write('abc\n_ my-img.png _ \ndef');
            this.model.removeInlineImage('my-img.png');

            assert.deepEqual([[0, 1, 2], [1]], this.changedLines);
        });
    });
});