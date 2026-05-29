'use strict';

import {TerminalModel} from '@/common/components/terminal/ansi/terminal_model';
import {Terminal} from '@/common/components/terminal/ansi/terminal_view';
import {removeElement} from '@/common/utils/common';
import {clearScreen, clearScreenDown, clearScreenUp, format, moveCursorUp, moveToPosition} from './terminal_test_utils';

function styledNode(text, styles = []) {
    return {
        'type': 'styledNode',
        'text': text,
        'styles': styles
    }
}

function styledComplexNode(styles = [], children) {
    return {
        'type': 'styledComplexNode',
        'styles': styles,
        'children': children
    }
}

function textNode(text) {
    return {
        'type': 'textNode',
        'text': text,
        'styles': []
    }
}

function anchorNode(url, styles = []) {
    return {
        'type': 'anchorNode',
        'text': url,
        'styles': styles,
        'href': url.replace(/\/+$/, '')
    }
}

function getElementClasses(element) {
    const classes = element.className.split(' ');
    removeElement(classes, '');
    return classes;
}

describe('Test terminal view', function () {
    let model, terminal;


    beforeAll(function () {

    });
    beforeEach(function () {
        model = new TerminalModel();
        terminal = new Terminal(model);
    });

    afterEach(function () {
    });
    afterAll(function () {
    });

    function getTextNodeText(textNode) {
        return textNode.nodeValue;
    }

    function getComplexNodeText(complexNode) {
        const firstChild = complexNode.childNodes[0];
        if (firstChild.nodeType === 1) {
            if (firstChild.tagName !== 'A') {
                throw Error('Unsupported child ' + firstChild);
            }
            return firstChild.innerText;
        }

        return getTextNodeText(firstChild);
    }

    function getText(element) {
        if (element.nodeType === 3) {
            return getTextNodeText(element);
        } else {
            return getComplexNodeText(element);
        }
    }

    function assertTextNode(element, text) {
        expect(element.nodeType).toBe(3)
        expect(getTextNodeText(element)).toBe(text)
    }

    function assertAnchor(element, href) {
        expect(element.tagName).toBe('A')
        expect(element.href.replace(/\/+$/, '')).toBe(href)
        expect(element.innerText).toBe(href)
    }

    function assertStyledNode(element, text, classes) {
        expect(element.nodeType).toBe(1)
        expect(element.tagName).toBe('SPAN')
        expect(getComplexNodeText(element)).toBe(text)

        const actualClasses = getElementClasses(element);
        expect(actualClasses).toEqual(classes)
    }

    function assertTexts(expectedTexts, element) {
        const actualTexts = [];
        for (let i = 0; i < element.childNodes.length; i++) {
            const lineElement = element.childNodes[i];

            let lineText = '';
            for (const textElement of lineElement.childNodes) {
                lineText += getText(textElement);
            }
            actualTexts.push(lineText);
        }

        expect(expectedTexts).toEqual(actualTexts)
    }

    function assertLine(lineElement, expectedNodes) {
        expect(lineElement.tagName).toBe('DIV')

        const actualNodes = [];
        for (const childNode of lineElement.childNodes) {
            const text = getText(childNode);

            if (childNode.nodeType === 3) {
                actualNodes.push(textNode(text));
                continue;
            }

            if (childNode.tagName === 'A') {
                actualNodes.push(anchorNode(text, []));
                continue;
            }

            expect(childNode.tagName).toBe('SPAN')

            const classes = getElementClasses(childNode);

            if (childNode.childNodes.length === 1) {
                if (childNode.childNodes[0].nodeType === 3) {
                    actualNodes.push(styledNode(text, classes));
                    continue;
                }

                expect(childNode.childNodes[0].tagName).toBe('A')
                actualNodes.push(anchorNode(text, classes));
                continue;
            }

            const grandChildrenNodes = [];
            for (const grandchild of childNode.childNodes) {
                if (grandchild.nodeType === 3) {
                    grandChildrenNodes.push(textNode(getTextNodeText(grandchild)));
                    continue;
                }

                expect(grandchild.tagName).toBe('A')
                grandChildrenNodes.push(anchorNode(getText(grandchild)));
            }
            actualNodes.push(styledComplexNode(classes, grandChildrenNodes));
        }

        expect(expectedNodes).toEqual(actualNodes)
    }

    function assertImageLine(lineElement, expectedSrc) {
        expect(lineElement.tagName).toBe('DIV')

        expect(lineElement.childNodes.length).toBe(1)
        expect(lineElement.childNodes[0].tagName).toBe('IMG')
        expect(lineElement.childNodes[0].getAttribute('src')).toBe(expectedSrc)
    }

    describe('change log content', function () {

        it('Test simple text', function () {
            model.write('some text');

            expect(terminal.element.childNodes.length).toBe(1)

            assertLine(terminal.element.childNodes[0], [textNode('some text')]);
        });

        it('Test styled text', function () {
            model.write(format(31) + '1234');

            expect(terminal.element.childNodes.length).toBe(1)
            assertLine(terminal.element.childNodes[0], [styledNode('1234', ['text_color_red'])]);
        });

        it('Test mixed styled text', function () {
            model.write('1234' + format(31, 1, 2) + 'abc' + format(42, 21) + '5' + format(0) + 'def');

            expect(terminal.element.childNodes.length).toBe(1)
            const lineElement = terminal.element.childNodes[0];

            assertLine(terminal.element.childNodes[0], [
                textNode('1234'),
                styledNode('abc', ['text_color_red', 'text_style_bold', 'text_style_dim']),
                styledNode('5', ['text_color_red', 'background_green', 'text_style_dim']),
                textNode('def')
            ]);
        });

        it('URL', function () {
            model.write('https://google.com');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [anchorNode('https://google.com')]);
        });

        it('URL between text', function () {
            model.write('begin http://wiki.org end');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [
                textNode('begin '),
                anchorNode('http://wiki.org'),
                textNode(' end')
            ]);
        });

        it('URL between styled text', function () {
            model.write(format(31) + 'begin' + format(0) + ' http://wiki.org ' + format(31) + 'end');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [
                styledNode('begin', ['text_color_red']),
                textNode(' '),
                anchorNode('http://wiki.org', []),
                textNode(' '),
                styledNode('end', ['text_color_red'])]);
        });

        it('Styled URL between texts', function () {
            model.write('begin' + format(31) + ' http://wiki.org ' + format(0) + 'end');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [
                textNode('begin'),
                styledComplexNode(['text_color_red'], [
                    textNode(' '),
                    anchorNode('http://wiki.org'),
                    textNode(' ')
                ]),
                textNode('end')]);
        });

        it('Unstyled URL after styled text', function () {
            model.write(format(31) + 'begin' + format(0) + ' http://wiki.org');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [
                styledNode('begin', ['text_color_red']),
                textNode(' '),
                anchorNode('http://wiki.org')]);
        });

        it('Append multiple separated URLs', function () {
            model.write('http://wiki.org, https://google.com,http://localhost:5000');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [
                anchorNode('http://wiki.org'),
                textNode(', '),
                anchorNode('https://google.com'),
                textNode(','),
                anchorNode('http://localhost:5000')
            ]);
        });

        it('Append complex URL', function () {
            model.write('http://api.plos.org/search'
                + '?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [anchorNode(
                'http://api.plos.org/search?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id')]);
        });

        it('Append colored URL', function () {
            model.write(format(31) + 'https://google.com');

            const lineElement = terminal.element.childNodes[0];

            assertLine(lineElement, [anchorNode('https://google.com', ['text_color_red'])]);
        });

        it('Replace single line', function () {
            model.write('some text');
            model.write('\rHello world');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [textNode('Hello world')]);
        });

        it('Replace line beginning', function () {
            model.write('some text\r');
            model.write('1234');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [textNode('1234 text')]);
        });

        it('Replace normal and styled element with plain text', function () {
            model.write('123 ' + format(31) + 'abc');
            model.write(format(0) + '\r0987654');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [textNode('0987654')]);
        });

        it('Replace normal and styled element with mixed text', function () {
            model.write('123 ' + format(31) + 'abc');
            model.write('\r0' + format(0) + '98' + format(32) + '76' + format(42) + '54');

            const lineElement = terminal.element.childNodes[0];
            assertLine(lineElement, [
                styledNode('0', ['text_color_red']),
                textNode('98'),
                styledNode('76', ['text_color_green']),
                styledNode('54', ['text_color_green', 'background_green'])
            ]);
        });

        it('Replace first line in multiline (complete)', function () {
            model.write('line1\nline2\n');
            model.write(moveCursorUp(2) + 'replacement');

            assertLine(terminal.element.childNodes[0], [textNode('replacement')]);
            assertLine(terminal.element.childNodes[1], [textNode('line2')])
        });

        it('Replace first line in multiline (middle)', function () {
            model.write('line1\n12' + moveCursorUp(1) + 'X');

            assertLine(terminal.element.childNodes[0], [textNode('liXe1')]);
            assertLine(terminal.element.childNodes[1], [textNode('12')])
        });

        it('Replace several lines in multiline', function () {
            model.write('line1\nline2\nline3\nline4\n');
            model.write(moveCursorUp(4) + 'a\nb\nlong line\n');

            assertTexts(['aine1', 'bine2', 'long line', 'line4'], terminal.element);
        });

        it('Replace at the line end', function () {
            model.write('line1\nline2' + moveCursorUp(1) + '987');

            assertTexts(['line1987', 'line2'], terminal.element);
        });

        it('Replace middle of Nth line', function () {
            model.write('line1\n');
            model.write('line2\n');
            model.write('abc');
            model.write('def');
            model.write('ghi\n');
            model.write('line4\n');
            model.write(moveCursorUp(2) + '9876');

            assertTexts(['line1', 'line2', '9876efghi', 'line4'], terminal.element);
        });

        it('Replace line multiple times', function () {
            model.write('lineX');

            for (var i = 0; i < 3; i++) {
                model.write('\r' + i + 'abc');
            }

            assertTexts(['2abcX'], terminal.element);
        });

        it('CR LF has no effect', function () {
            model.write('123\r\n456');

            assertTexts(['123', '456'], terminal.element);
        });

        it('Replace empty line after multiple newlines', function () {
            model.write('123\n\n\n\n456\r' + moveCursorUp(2) + 'abc');

            assertTexts(['123', '', 'abc', '', '456'], terminal.element);
        });

    });

    describe('Test clear screen commands', function () {

        it('Test clear all', function () {
            model.write('123\n456\n789\n' + moveToPosition(1, 1) + clearScreen() + 'abc');

            expect(terminal.element.childNodes.length).toBe(1)
            assertLine(terminal.element.childNodes[0], [textNode('abc')]);
        });

        it('Test clear all, when separate writes', function () {
            model.write('123\n456\n789\n' + moveToPosition(1, 1));
            model.write(clearScreen() + 'abc');

            expect(terminal.element.childNodes.length).toBe(1)
            assertLine(terminal.element.childNodes[0], [textNode('abc')]);
        });

        it('Test clear to the bottom', function () {
            model.write('123\n45\n6\n7890\n' + moveToPosition(1, 1) + clearScreenDown() + 'abc\nd');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode('123')]);
            assertLine(terminal.element.childNodes[1], [textNode('4abc')]);
            assertLine(terminal.element.childNodes[2], [textNode('d')]);
        });

        it('Test clear to the bottom, when separate writes', function () {
            model.write('123\n45\n6\n7890\n' + moveToPosition(1, 1));
            model.write(clearScreenDown() + 'abc\nd');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode('123')]);
            assertLine(terminal.element.childNodes[1], [textNode('4abc')]);
            assertLine(terminal.element.childNodes[2], [textNode('d')]);
        });

        it('Test clear to the bottom, when line below is empty', function () {
            model.write('123\n45\n' + clearScreenDown() + 'abc');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode('123')]);
            assertLine(terminal.element.childNodes[1], [textNode('45')]);
            assertLine(terminal.element.childNodes[2], [textNode('abc')]);
        });

        it('Test clear to the bottom, when line below is empty and separate writes', function () {
            model.write('123\n45\n');
            model.write(clearScreenDown() + 'abc');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode('123')]);
            assertLine(terminal.element.childNodes[1], [textNode('45')]);
            assertLine(terminal.element.childNodes[2], [textNode('abc')]);
        });


        it('Test clear to the top', function () {
            model.write('123\n345\n67\n890\n' + moveToPosition(1, 1) + clearScreenUp() + 'abc\nd');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode(' abc')]);
            assertLine(terminal.element.childNodes[1], [textNode('d7')]);
            assertLine(terminal.element.childNodes[2], [textNode('890')]);
        });

        it('Test clear to the top, when separate writes', function () {
            model.write('123\n345\n67\n890\n' + moveToPosition(1, 1));
            model.write(clearScreenUp() + 'abc\nd');

            expect(terminal.element.childNodes.length).toBe(3)
            assertLine(terminal.element.childNodes[0], [textNode(' abc')]);
            assertLine(terminal.element.childNodes[1], [textNode('d7')]);
            assertLine(terminal.element.childNodes[2], [textNode('890')]);
        });
    });

    describe('Test inline images', function () {

        it('Test when one line and image available before text', function () {
            model.setInlineImage('/home/me/test.png', 'my-img.png');
            model.write('/home/me/test.png');

            expect(terminal.element.childNodes.length).toBe(1)
            assertImageLine(terminal.element.childNodes[0], 'my-img.png');
        });

        it('Test when one line and image available after text', function () {
            model.write('/home/me/test.png');
            model.setInlineImage('/home/me/test.png', 'my-img.png');

            expect(terminal.element.childNodes.length).toBe(1)
            assertImageLine(terminal.element.childNodes[0], 'my-img.png');
        });

        it('Test when multiline and image available after text', function () {
            model.write('abc\nde\nf');
            model.write('\n123/home/me/test.png456\nghi');
            model.write('jkl\nmno');
            model.setInlineImage('/home/me/test.png', 'my-img.png');

            expect(terminal.element.childNodes.length).toBe(6)
            assertImageLine(terminal.element.childNodes[3], 'my-img.png');
            assertLine(terminal.element.childNodes[2], [textNode('f')]);
            assertLine(terminal.element.childNodes[4], [textNode('ghijkl')]);
        });

        it('Test absolute url', function () {
            const downloadUrl = 'http://localhost:8080/images/my-img.png';
            model.setInlineImage('/home/me/test.png', downloadUrl);
            model.write('/home/me/test.png');

            expect(terminal.element.childNodes.length).toBe(1)
            assertImageLine(terminal.element.childNodes[0], downloadUrl);
        });

        it('Test remove inline image', function () {
            model.setInlineImage('/home/me/test.png', 'my-img.png');
            model.write('/home/me/test.png');
            model.removeInlineImage('/home/me/test.png');

            expect(terminal.element.childNodes.length).toBe(1)
            assertLine(terminal.element.childNodes[0], [textNode('/home/me/test.png')]);
        });

        it('Test different images', function () {
            model.setInlineImage('/home/me/test1.png', '/images/img1.png');
            model.write('/home/me/test1.png\nabc');
            model.write(' /home/me/test2.png def \n');
            model.write(' hij \n');
            model.setInlineImage('/home/me/test2.png', '/images/img2.png');
            model.write('_ /home/me/test1.png _');

            expect(terminal.element.childNodes.length).toBe(4)
            assertImageLine(terminal.element.childNodes[0], '/images/img1.png');
            assertImageLine(terminal.element.childNodes[1], '/images/img2.png');
            assertImageLine(terminal.element.childNodes[3], '/images/img1.png');
        });
    });
});