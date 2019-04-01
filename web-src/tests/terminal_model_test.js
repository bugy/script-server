'use strict';

import {assert, config as chaiConfig} from 'chai';
import {isNull} from '../js/common';
import {Style, StyledRange, TerminalModel} from '../js/components/terminal/terminal_model';
import {format, moveCursorDown, moveCursorLeft, moveCursorRight, moveCursorUp} from './terminal_test_utils';

chaiConfig.truncateThreshold = 0;

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
            const changedLinesField = [];
            this.changedLines = changedLinesField;

            this.model.addListener({
                linesChanges: function (changedLines) {
                    changedLinesField.push(changedLines);
                },

                cleared: function () {

                }
            });
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

            assert.deepEqual(['1', ' abc'], this.model.lines);
        });

        it('Test move cursor down N to unexisting line', function () {
            this.model.write('12345' + moveCursorDown(3) + 'a');

            assert.deepEqual(['12345', '', '', '     a'], this.model.lines);
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
});