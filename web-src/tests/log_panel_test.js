"use strict";

var assert = chai.assert;
chai.config.truncateThreshold = 0;

describe('Test logPanel', function () {

    before(function () {

    });
    beforeEach(function () {
        this.logPanel = new logPanelComponent({}).$mount();
        this.logContent = this.logPanel.$refs.logContent;
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
            this.logPanel.setLog('some text');

            assert.equal(1, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[0], 'some text');
        });

        it('Append text log', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('|another text');
            assert.equal(2, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[1], '|another text');
        });

        it('Append URL', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('https://google.com');
            assert.equal(2, this.logContent.childNodes.length);
            assertAnchor(this.logContent.childNodes[1], 'https://google.com');
        });

        it('Append URL inside text', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('begin http://wiki.org end');
            assert.equal(2, this.logContent.childNodes.length);

            let textContainer = this.logContent.childNodes[1];
            assertTextNode(textContainer.childNodes[0], 'begin ');
            assertAnchor(textContainer.childNodes[1], 'http://wiki.org');
            assertTextNode(textContainer.childNodes[2], ' end');
        });

        it('Append multiple separated URLs', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('http://wiki.org, https://google.com,http://localhost:5000');
            assert.equal(2, this.logContent.childNodes.length);

            let textContainer = this.logContent.childNodes[1];
            assertAnchor(textContainer.childNodes[0], 'http://wiki.org');
            assertTextNode(textContainer.childNodes[1], ', ');
            assertAnchor(textContainer.childNodes[2], 'https://google.com');
            assertTextNode(textContainer.childNodes[3], ',');
            assertAnchor(textContainer.childNodes[4], 'http://localhost:5000');
        });

        it('Append complex URL', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('http://api.plos.org/search'
                + '?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id');
            assert.equal(2, this.logContent.childNodes.length);
            assertAnchor(this.logContent.childNodes[1],
                'http://api.plos.org/search?q=title:%22Drosophila%22%20and%20body:%22RNA%22&fl=id');
        });

        it('Append colored URL', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('https://google.com', 'red');
            assert.equal(2, this.logContent.childNodes.length);

            let formattedContainer = this.logContent.childNodes[1];
            assert.equal(1, formattedContainer.nodeType);
            assertAnchor(formattedContainer.childNodes[0], 'https://google.com');
            assert.equal('text_color_red', formattedContainer.className);
        });

        it('Append colored log', function () {
            this.logPanel.setLog('some text');

            this.logPanel.appendLog('|colored text', 'red');
            assert.equal(2, this.logContent.childNodes.length);
            assertComplexNode(this.logContent.childNodes[1], '|colored text', 'text_color_red');
        });

        it('Replace single line', function () {
            this.logPanel.setLog('some text');

            this.logPanel.replaceLog('_another_', null, null, null, 0, 0);
            assert.equal(1, this.logContent.childNodes.length);
            assertTextNode(this.logContent.childNodes[0], '_another_');
        });

        it('Replace line beginning', function () {
            this.logPanel.setLog('some text');

            this.logPanel.replaceLog('_NEW_', null, null, null, 0, 0);

            assertTexts(this.logContent, ['_NEW_', 'text']);
        });

        it('Replace line end', function () {
            this.logPanel.setLog('some text');

            this.logPanel.replaceLog('_NEW_', null, null, null, 4, 0);

            assertTexts(this.logContent, ['some', '_NEW_']);
        });

        it('Replace line middle', function () {
            this.logPanel.setLog('some text');

            this.logPanel.replaceLog('12345', null, null, null, 2, 0);

            assertTexts(this.logContent, ['so', '12345', 'xt']);
        });

        it('Replace 2 elements', function () {
            this.logPanel.setLog('123');
            this.logPanel.appendLog('456');

            this.logPanel.replaceLog('abcdef', null, null, null, 0, 0);

            assertTexts(this.logContent, ['abcdef']);
        });

        it('Replace 3 elements in middle', function () {
            this.logPanel.setLog('123');
            this.logPanel.appendLog('456');
            this.logPanel.appendLog('789');

            this.logPanel.replaceLog('abcdef', null, null, null, 1, 0);

            assertTexts(this.logContent, ['1', 'abcdef', '89']);
        });

        it('Replace first line in multiline (complete)', function () {
            this.logPanel.setLog('line1\nline2');

            this.logPanel.replaceLog('replacement', null, null, null, 0, 0);

            assertTexts(this.logContent, ['replacement\n', 'line2']);
        });

        it('Replace first line in multiline (middle)', function () {
            this.logPanel.setLog('line1\nline2');

            this.logPanel.replaceLog('X', null, null, null, 2, 0);

            assertTexts(this.logContent, ['li', 'X', 'e1\nline2']);
        });

        it('Replace several lines in multiline', function () {
            this.logPanel.setLog('line1\nline2\nline3\nline4');

            this.logPanel.replaceLog('a\nb\nlong line\n', null, null, null, 2, 0);

            assertTexts(this.logContent, ['li', 'a', 'e1\n', 'b', 'ine2\n', 'long line\n', 'line4']);
        });

        it('Replace at the line end', function () {
            this.logPanel.setLog('line1\n');

            this.logPanel.replaceLog('a', null, null, null, 5, 0);

            assertTexts(this.logContent, ['line1', 'a\n']);
        });

        it('Replace multiline in several multiline elements', function () {
            this.logPanel.setLog('line1\n');
            this.logPanel.appendLog('line2\nlin');
            this.logPanel.appendLog('e3\nl\nine4');

            this.logPanel.replaceLog('a\nb\nlong line\n', null, null, null, 5, 0);

            assertTexts(this.logContent, ['line1', 'a\nb', 'ine2\n', 'long line\n', 'l\nine4']);
        });

        it('Replace 2nd line from 2', function () {
            this.logPanel.setLog('line1\n');
            this.logPanel.appendLog('line2');

            this.logPanel.replaceLog('REPLACE', null, null, null, 0, 1);

            assertTexts(this.logContent, ['line1\n', 'REPLACE']);
        });

        it('Replace 2nd line from 3', function () {
            this.logPanel.setLog('line1\n');
            this.logPanel.appendLog('line2\n');
            this.logPanel.appendLog('line3');

            this.logPanel.replaceLog('REPLACE', null, null, null, 0, 1);

            assertTexts(this.logContent, ['line1\n', 'REPLACE\n', 'line3']);
        });

        it('Replace middle of Nth complex line', function () {
            this.logPanel.setLog('line1\n');
            this.logPanel.appendLog('line2\n');
            this.logPanel.appendLog('abc');
            this.logPanel.appendLog('def');
            this.logPanel.appendLog('ghi\n');
            this.logPanel.appendLog('line4');

            this.logPanel.replaceLog('OPQRS', null, null, null, 2, 2);

            assertTexts(this.logContent, ['line1\n', 'line2\n', 'ab', 'OPQRS', 'hi\n', 'line4']);
        });

        it('Replace line multiple times', function () {
            this.logPanel.setLog('line1\n');

            for (var i = 0; i < 3; i++) {
                this.logPanel.replaceLog('REPL' + i, null, null, null, 0, 0);
            }

            assertTexts(this.logContent, ['REPL2\n']);
        });

        it('Replace last line multiple times', function () {
            this.logPanel.setLog('line1\n');
            this.logPanel.appendLog('line2\n');
            this.logPanel.appendLog('line3\n');

            for (var i = 0; i < 3; i++) {
                this.logPanel.replaceLog('REPL' + i, null, null, null, 0, 2);
            }

            assertTexts(this.logContent, ['line1\n', 'line2\n', 'REPL2\n']);
        });

        it('Replace first line in multiline without text', function () {
            this.logPanel.setLog('\n');
            this.logPanel.appendLog('\n');
            this.logPanel.appendLog('\n');

            this.logPanel.replaceLog('some text', null, null, null, 0, 0);

            assertTexts(this.logContent, ['some text\n', '\n', '\n']);
        });

        it('Replace 2nd line in multiline without text', function () {
            this.logPanel.setLog('\n');
            this.logPanel.appendLog('\n');
            this.logPanel.appendLog('\n');

            this.logPanel.replaceLog('some text', null, null, null, 0, 1);

            assertTexts(this.logContent, ['\n', 'some text\n', '\n']);
        });

        it('Replace last line in multiline without text', function () {
            this.logPanel.setLog('\n');
            this.logPanel.appendLog('\n');
            this.logPanel.appendLog('\n');

            this.logPanel.replaceLog('some text', null, null, null, 0, 2);

            assertTexts(this.logContent, ['\n', '\n', 'some text\n']);
        });

        it('Replace newlines with newlines only', function () {
            this.logPanel.setLog('\n\n');
            this.logPanel.appendLog('\n');
            this.logPanel.appendLog('\n');

            this.logPanel.replaceLog('\n\n', null, null, null, 0, 0);

            assertTexts(this.logContent, ['\n\n', '\n', '\n']);
        });

        it('Replace split formatted text by replace', function () {
            this.logPanel.setLog('');
            this.logPanel.appendLog('some very long line', 'red', 'blue', ['bold']);

            this.logPanel.replaceLog('OOPS', null, null, null, 5, 0);

            assertComplexNode(this.logContent.childNodes[0], 'some ', 'text_color_red background_blue text_style_bold');
            assertTextNode(this.logContent.childNodes[1], 'OOPS');
            assertComplexNode(this.logContent.childNodes[2], ' long line', 'text_color_red background_blue text_style_bold');
        });

        it('Replace with formatted text', function () {
            this.logPanel.setLog('some very long line');

            this.logPanel.replaceLog('OOPS', null, 'green', null, 5, 0);

            assertTextNode(this.logContent.childNodes[0], 'some ');
            assertComplexNode(this.logContent.childNodes[1], 'OOPS', 'background_green');
            assertTextNode(this.logContent.childNodes[2], ' long line');
        });

        it('Replace with new line and then some text', function () {
            this.logPanel.setLog('line1\nline2');
            this.logPanel.replaceLog('\ntest', null, null, null, 0, 1);
            this.logPanel.replaceLog('hello', null, null, null, 0, 2);

            assertTexts(this.logContent, ['line1\nline2\n', 'hello'])
        })
    })
});