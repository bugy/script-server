'use strict';

import {mount} from 'vue-test-utils';
import {hasClass, isEmptyString} from '../js/common';
import LogPanel from '../js/components/log_panel'
import {vueTicks, wrapVModel} from './test_utils';

var assert = chai.assert;
chai.config.truncateThreshold = 0;

describe('Test logPanel', function () {

    before(function () {

    });
    beforeEach(function () {
        this.logPanel = mount(LogPanel, {});
        this.logContent = this.logPanel.vm.$refs.logContent;
    });

    afterEach(function () {
    });
    after(function () {
    });

    function getTextNodeText(textNode) {
        return textNode.nodeValue;
    }

    function getComplexNodeText(complexNode) {
        return getTextNodeText(complexNode.childNodes[0]);
    }

    function getText(element) {
        if (element.nodeType === 3) {
            return getTextNodeText(element);
        } else {
            return getComplexNodeText(element);
        }
    }

    function assertTextNode(element, text) {
        assert.equal(3, element.nodeType);
        assert.equal(text, getTextNodeText(element));
    }

    function assertAnchor(element, href) {
        assert.equal('A', element.tagName);
        assert.equal(href, element.href.replace(/\/+$/, ''));
        assert.equal(href, element.innerText);
    }

    function assertComplexNode(element, text, className) {
        assert.equal(1, element.nodeType);
        assert.equal(text, getComplexNodeText(element));
        assert.equal(className, element.className);
    }

    function assertTexts(logContent, expectedTexts) {
        var actualTexts = [];
        for (var i = 0; i < logContent.childNodes.length; i++) {
            var childText = getText(logContent.childNodes[i]);
            actualTexts.push(childText);
        }

        assert.deepEqual(expectedTexts, actualTexts);
    }

    describe('change log content', function () {

        it('Set log', function () {
            this.logPanel.vm.setLog('some text');

            assert.equal(1, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[0], 'some text');
        });

        it('Append text log', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('|another text');
            assert.equal(2, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[1], '|another text');
        });

        it('Append URL', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('https://google.com');
            assert.equal(2, this.logContent.childNodes.length);
            assertAnchor(this.logContent.childNodes[1], 'https://google.com');
        });

        it('Append URL inside text', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('begin http://wiki.org end');
            assert.equal(2, this.logContent.childNodes.length);

            let textContainer = this.logContent.childNodes[1];
            assertTextNode(textContainer.childNodes[0], 'begin ');
            assertAnchor(textContainer.childNodes[1], 'http://wiki.org');
            assertTextNode(textContainer.childNodes[2], ' end');
        });

        it('Append multiple separated URLs', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('http://wiki.org, https://google.com,http://localhost:5000');
            assert.equal(2, this.logContent.childNodes.length);

            let textContainer = this.logContent.childNodes[1];
            assertAnchor(textContainer.childNodes[0], 'http://wiki.org');
            assertTextNode(textContainer.childNodes[1], ', ');
            assertAnchor(textContainer.childNodes[2], 'https://google.com');
            assertTextNode(textContainer.childNodes[3], ',');
            assertAnchor(textContainer.childNodes[4], 'http://localhost:5000');
        });

        it('Append complex URL', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('http://api.plos.org/search'
                + '?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id');
            assert.equal(2, this.logContent.childNodes.length);
            assertAnchor(this.logContent.childNodes[1],
                'http://api.plos.org/search?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id');
        });

        it('Append colored URL', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('https://google.com', 'red');
            assert.equal(2, this.logContent.childNodes.length);

            let formattedContainer = this.logContent.childNodes[1];
            assert.equal(1, formattedContainer.nodeType);
            assertAnchor(formattedContainer.childNodes[0], 'https://google.com');
            assert.equal('text_color_red', formattedContainer.className);
        });

        it('Append colored log', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.appendLog('|colored text', 'red');
            assert.equal(2, this.logContent.childNodes.length);
            assertComplexNode(this.logContent.childNodes[1], '|colored text', 'text_color_red');
        });

        it('Replace single line', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.replaceLog('_another_', null, null, null, 0, 0);
            assert.equal(1, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[0], '_another_');
        });

        it('Replace line beginning', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.replaceLog('_NEW_', null, null, null, 0, 0);

            assertTexts(this.logContent, ['_NEW_', 'text']);
        });

        it('Replace line end', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.replaceLog('_NEW_', null, null, null, 4, 0);

            assertTexts(this.logContent, ['some', '_NEW_']);
        });

        it('Replace line middle', function () {
            this.logPanel.vm.setLog('some text');

            this.logPanel.vm.replaceLog('12345', null, null, null, 2, 0);

            assertTexts(this.logContent, ['so', '12345', 'xt']);
        });

        it('Replace 2 elements', function () {
            this.logPanel.vm.setLog('123');
            this.logPanel.vm.appendLog('456');

            this.logPanel.vm.replaceLog('abcdef', null, null, null, 0, 0);

            assertTexts(this.logContent, ['abcdef']);
        });

        it('Replace 3 elements in middle', function () {
            this.logPanel.vm.setLog('123');
            this.logPanel.vm.appendLog('456');
            this.logPanel.vm.appendLog('789');

            this.logPanel.vm.replaceLog('abcdef', null, null, null, 1, 0);

            assertTexts(this.logContent, ['1', 'abcdef', '89']);
        });

        it('Replace first line in multiline (complete)', function () {
            this.logPanel.vm.setLog('line1\nline2');

            this.logPanel.vm.replaceLog('replacement', null, null, null, 0, 0);

            assertTexts(this.logContent, ['replacement\n', 'line2']);
        });

        it('Replace first line in multiline (middle)', function () {
            this.logPanel.vm.setLog('line1\nline2');

            this.logPanel.vm.replaceLog('X', null, null, null, 2, 0);

            assertTexts(this.logContent, ['li', 'X', 'e1\nline2']);
        });

        it('Replace several lines in multiline', function () {
            this.logPanel.vm.setLog('line1\nline2\nline3\nline4');

            this.logPanel.vm.replaceLog('a\nb\nlong line\n', null, null, null, 2, 0);

            assertTexts(this.logContent, ['li', 'a', 'e1\n', 'b', 'ine2\n', 'long line\n', 'line4']);
        });

        it('Replace at the line end', function () {
            this.logPanel.vm.setLog('line1\n');

            this.logPanel.vm.replaceLog('a', null, null, null, 5, 0);

            assertTexts(this.logContent, ['line1', 'a\n']);
        });

        it('Replace multiline in several multiline elements', function () {
            this.logPanel.vm.setLog('line1\n');
            this.logPanel.vm.appendLog('line2\nlin');
            this.logPanel.vm.appendLog('e3\nl\nine4');

            this.logPanel.vm.replaceLog('a\nb\nlong line\n', null, null, null, 5, 0);

            assertTexts(this.logContent, ['line1', 'a\nb', 'ine2\n', 'long line\n', 'l\nine4']);
        });

        it('Replace 2nd line from 2', function () {
            this.logPanel.vm.setLog('line1\n');
            this.logPanel.vm.appendLog('line2');

            this.logPanel.vm.replaceLog('REPLACE', null, null, null, 0, 1);

            assertTexts(this.logContent, ['line1\n', 'REPLACE']);
        });

        it('Replace 2nd line from 3', function () {
            this.logPanel.vm.setLog('line1\n');
            this.logPanel.vm.appendLog('line2\n');
            this.logPanel.vm.appendLog('line3');

            this.logPanel.vm.replaceLog('REPLACE', null, null, null, 0, 1);

            assertTexts(this.logContent, ['line1\n', 'REPLACE\n', 'line3']);
        });

        it('Replace middle of Nth complex line', function () {
            this.logPanel.vm.setLog('line1\n');
            this.logPanel.vm.appendLog('line2\n');
            this.logPanel.vm.appendLog('abc');
            this.logPanel.vm.appendLog('def');
            this.logPanel.vm.appendLog('ghi\n');
            this.logPanel.vm.appendLog('line4');

            this.logPanel.vm.replaceLog('OPQRS', null, null, null, 2, 2);

            assertTexts(this.logContent, ['line1\n', 'line2\n', 'ab', 'OPQRS', 'hi\n', 'line4']);
        });

        it('Replace line multiple times', function () {
            this.logPanel.vm.setLog('line1\n');

            for (var i = 0; i < 3; i++) {
                this.logPanel.vm.replaceLog('REPL' + i, null, null, null, 0, 0);
            }

            assertTexts(this.logContent, ['REPL2\n']);
        });

        it('Replace last line multiple times', function () {
            this.logPanel.vm.setLog('line1\n');
            this.logPanel.vm.appendLog('line2\n');
            this.logPanel.vm.appendLog('line3\n');

            for (var i = 0; i < 3; i++) {
                this.logPanel.vm.replaceLog('REPL' + i, null, null, null, 0, 2);
            }

            assertTexts(this.logContent, ['line1\n', 'line2\n', 'REPL2\n']);
        });

        it('Replace first line in multiline without text', function () {
            this.logPanel.vm.setLog('\n');
            this.logPanel.vm.appendLog('\n');
            this.logPanel.vm.appendLog('\n');

            this.logPanel.vm.replaceLog('some text', null, null, null, 0, 0);

            assertTexts(this.logContent, ['some text\n', '\n', '\n']);
        });

        it('Replace 2nd line in multiline without text', function () {
            this.logPanel.vm.setLog('\n');
            this.logPanel.vm.appendLog('\n');
            this.logPanel.vm.appendLog('\n');

            this.logPanel.vm.replaceLog('some text', null, null, null, 0, 1);

            assertTexts(this.logContent, ['\n', 'some text\n', '\n']);
        });

        it('Replace last line in multiline without text', function () {
            this.logPanel.vm.setLog('\n');
            this.logPanel.vm.appendLog('\n');
            this.logPanel.vm.appendLog('\n');

            this.logPanel.vm.replaceLog('some text', null, null, null, 0, 2);

            assertTexts(this.logContent, ['\n', '\n', 'some text\n']);
        });

        it('Replace newlines with newlines only', function () {
            this.logPanel.vm.setLog('\n\n');
            this.logPanel.vm.appendLog('\n');
            this.logPanel.vm.appendLog('\n');

            this.logPanel.vm.replaceLog('\n\n', null, null, null, 0, 0);

            assertTexts(this.logContent, ['\n\n', '\n', '\n']);
        });

        it('Replace split formatted text by replace', function () {
            this.logPanel.vm.setLog('');
            this.logPanel.vm.appendLog('some very long line', 'red', 'blue', ['bold']);

            this.logPanel.vm.replaceLog('OOPS', null, null, null, 5, 0);

            assertComplexNode(this.logContent.childNodes[0], 'some ', 'text_color_red background_blue text_style_bold');
            assertTextNode(this.logContent.childNodes[1], 'OOPS');
            assertComplexNode(this.logContent.childNodes[2], ' long line', 'text_color_red background_blue text_style_bold');
        });

        it('Replace with formatted text', function () {
            this.logPanel.vm.setLog('some very long line');

            this.logPanel.vm.replaceLog('OOPS', null, 'green', null, 5, 0);

            assertTextNode(this.logContent.childNodes[0], 'some ');
            assertComplexNode(this.logContent.childNodes[1], 'OOPS', 'background_green');
            assertTextNode(this.logContent.childNodes[2], ' long line');
        });

        it('Replace with new line and then some text', function () {
            this.logPanel.vm.setLog('line1\nline2');
            this.logPanel.vm.replaceLog('\ntest', null, null, null, 0, 1);
            this.logPanel.vm.replaceLog('hello', null, null, null, 0, 2);

            assertTexts(this.logContent, ['line1\nline2\n', 'hello'])
        })
    })
});