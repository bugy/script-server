'use strict';

var logPanelComponent;

(function () {

    var urlRegex = new RegExp('https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}' +
        '(\\.*([-a-zA-Z0-9@:%_\+~#?//=])+(&amp;)?)*',
        'g');

    function getLogElementTextNode(logElement) {
        if (logElement.nodeType === 3) {
            return logElement;
        } else {
            for (var i = 0; i < logElement.childNodes.length; i++) {
                if (logElement.childNodes[i].nodeType === 3) {
                    return logElement.childNodes[i];
                }
            }
            return null;
        }
    }

    function getLogElementText(logElement) {
        return getLogElementTextNode(logElement).nodeValue;
    }

    function setLogElementText(logElement, text) {
        getLogElementTextNode(logElement).nodeValue = text;
    }

    function _findFirstElementAtLine(logContent, y) {
        var firstMatchingElement = null;
        for (var i = logContent.childNodes.length - 1; i >= 0; i--) {
            var child = logContent.childNodes[i];
            if (child.firstLine > y) {
                continue;
            } else if (child.lastLine < y) {
                break;
            }
            firstMatchingElement = child;
        }
        return firstMatchingElement;
    }

    function _createLinesFromElements(firstLine, maxLinesCount, startingElement) {
        var currentLines = [];
        var lastLine = firstLine + maxLinesCount;
        for (var i = firstLine; i <= lastLine; i++) {
            currentLines.push([]);
        }

        var currentElement = startingElement;
        var currentLine = startingElement.firstLine;

        while (!isNull(currentElement) && (currentElement.firstLine <= lastLine)) {
            var currentIndex = 0;
            var currentElementText = getLogElementText(currentElement);

            while ((currentIndex >= 0) && (currentIndex < currentElementText.length) && (currentLine <= lastLine)) {
                var nextIndex = currentElementText.indexOf('\n', currentIndex);

                var linesOffset = currentLine - firstLine;
                if (linesOffset >= 0) {
                    var lineText;
                    var end;
                    var hasNextLine;
                    if (nextIndex < 0) {
                        lineText = currentElementText.substr(currentIndex);
                        end = currentElementText.length;
                        hasNextLine = !isNull(currentElement.nextSibling);
                    } else {
                        lineText = currentElementText.substring(currentIndex, nextIndex);
                        end = nextIndex + 1;
                        hasNextLine = true;
                    }

                    var line = currentLines[linesOffset];
                    line.hasNextLine = hasNextLine;
                    line.push({
                        'text': lineText,
                        'element': currentElement,
                        'start': currentIndex,
                        'end': end
                    });
                }

                if (nextIndex < 0) {
                    break;
                }

                currentLine++;
                currentIndex = nextIndex + 1;
            }

            currentElement = currentElement.nextSibling;
        }

        return currentLines;
    }

    function _replaceInLines(x, text, currentLines) {
        var xOffset = x;

        var incomingLines = text.split(/\n/);

        for (var lineIndex = 0; lineIndex < incomingLines.length; lineIndex++) {
            var incomingLine = incomingLines[lineIndex];

            if (incomingLine === '') {
                xOffset = 0;
                continue;
            }

            var existingLine = currentLines[lineIndex];

            var currentLinePosition = 0;
            var incomingLinePosition = 0;

            for (var chunkIndex = 0; chunkIndex < existingLine.length; chunkIndex++) {
                var chunk = existingLine[chunkIndex];
                var chunkLength = chunk.text.length;
                var chunkReplaceOffset = 0;

                if (currentLinePosition < xOffset) {
                    chunkReplaceOffset = Math.min(xOffset - currentLinePosition, chunkLength);
                    currentLinePosition += chunkReplaceOffset;
                }

                if (chunkReplaceOffset >= chunkLength) {
                    continue;
                }

                if (chunkReplaceOffset > 0) {
                    var newChunk = {
                        'text': chunk.text.substr(0, chunkReplaceOffset),
                        'element': chunk.element,
                        'start': chunk.start,
                        'end': chunk.start + chunkReplaceOffset
                    };
                    existingLine.splice(chunkIndex, 0, newChunk);
                    chunk.text = chunk.text.substr(chunkReplaceOffset);
                    chunk.start = chunk.start + chunkReplaceOffset;
                    chunkLength = chunk.text.length;
                    chunkIndex++;
                }

                var chunkReplaceLength = Math.min(
                    chunkLength,
                    incomingLine.length - incomingLinePosition);

                if (chunkReplaceLength > 0) {
                    chunk.text = chunk.text.substr(chunkReplaceLength);

                    incomingLinePosition += chunkReplaceLength;
                }

                if (incomingLinePosition >= incomingLine.length) {
                    break;
                }
            }

            var incomingLineChunk = {
                'text': incomingLine
            };
            existingLine.splice(chunkIndex, 0, incomingLineChunk);

            xOffset = 0;
        }
    }

    function _appendNewLineCharacter(linesArray) {
        for (var i = 0; i < linesArray.length; i++) {
            var line = linesArray[i];

            if ((i === linesArray.length - 1) && (!line.hasNextLine)) {
                break;
            }

            var added = false;

            for (var chunkIndex = line.length - 1; chunkIndex >= 0; chunkIndex--) {
                var chunk = line[chunkIndex];
                if (chunk.text.length > 0) {
                    if (chunk.text.indexOf('\n') === -1) {
                        chunk.text += '\n';
                    }
                    added = true;
                    break;
                }
            }

            if (!added) {
                if (line.length > 0) {
                    var lastChunk = line[line.length - 1];
                    lastChunk.text += '\n';
                } else {
                    line.push({'text': '\n'});
                }
            }
        }
    }

    function _findLastChunkWithElement(lines) {
        for (var i = lines.length - 1; i >= 0; i--) {
            var line = lines[i];

            for (var j = line.length - 1; j >= 0; j--) {
                var chunk = line[j];
                if (!isNull(chunk.element)) {
                    return chunk;
                }
            }
        }

        return null;
    }

    function _updateElementsFromLines(lines, container, newElementCreator) {
        var visitedElements = [];
        var currentElement = null;
        var prevElementNew = false;

        var lastChunk = _findLastChunkWithElement(lines);
        if (!isNull(lastChunk)) {
            if (lastChunk.end < getLogElementText(lastChunk.element).length) {
                currentElement = lastChunk.element;
            } else {
                currentElement = lastChunk.element.nextSibling;
            }
        }

        function appendNewElement(newElement) {
            if (isNull(currentElement)) {
                container.appendChild(newElement);
            } else {
                container.insertBefore(newElement, currentElement);
            }
        }

        var elementReplacements = new Hashtable();

        for (var i = lines.length - 1; i >= 0; i--) {
            var line = lines[i];

            for (var j = line.length - 1; j >= 0; j--) {
                var chunk = line[j];

                var chunkElement = chunk.element;

                if (chunkElement == null) {
                    if (prevElementNew) {
                        var currentText = getLogElementText(currentElement);
                        currentText = chunk.text + currentText;
                        setLogElementText(currentElement, currentText);
                    } else {
                        var newElement = newElementCreator(chunk.text);
                        appendNewElement(newElement);
                        currentElement = newElement;
                    }

                    prevElementNew = true;

                } else {

                    chunkElement.linesCount = null;

                    prevElementNew = false;

                    if (elementReplacements.containsKey(chunkElement)) {
                        chunkElement = elementReplacements.get(chunkElement);
                    }

                    if ((chunkElement !== currentElement) && (contains(visitedElements, chunkElement))) {
                        var fullElementText = getLogElementText(chunkElement);
                        var endPart = fullElementText.substr(chunk.end);

                        if (endPart === '') {
                            container.insertBefore(chunkElement, currentElement);
                        } else {
                            setLogElementText(chunkElement, endPart);

                            var newElement = chunkElement.cloneNode(true);
                            appendNewElement(newElement);
                            elementReplacements.put(chunk.element, newElement);
                            chunkElement = newElement;
                        }

                        setLogElementText(chunkElement, fullElementText.substr(0, chunk.end));
                    }

                    if (!contains(visitedElements, chunkElement)) {
                        visitedElements.push(chunkElement);
                    }

                    var elementText = getLogElementText(chunkElement);
                    var updatedElementText = '';
                    if (chunk.start > 0) {
                        updatedElementText += elementText.substr(0, chunk.start);
                    }
                    updatedElementText += chunk.text;
                    if (elementText.length > chunk.end) {
                        updatedElementText += elementText.substr(chunk.end);
                    }

                    if (updatedElementText !== '') {
                        setLogElementText(chunkElement, updatedElementText);
                        currentElement = chunkElement;
                    } else {
                        container.removeChild(chunkElement);
                    }
                }
            }
        }
    }

    //noinspection JSAnnotator
    logPanelComponent = Vue.component('log-panel', {
        template: ''
            + '<div class="log-panel">'
            + '    <code class="log-content" '
            + '        v-on:scroll="recalculateScrollPosition" '
            + '        ref="logContent"'
            + '        v-on:mousedown="mouseDown = true"'
            + '        v-on:mouseup="mouseDown = false"></code>'
            + '    <div class="log-panel-shadow" v-bind:class="{'
            + '            \'shadow-top\': !atTop && atBottom,'
            + '            \'shadow-bottom\': atTop && !atBottom,'
            + '            \'shadow-top-bottom\': !atTop && !atBottom'
            + '        }">'
            + '        '
            + '    </div>'
            + '</div>',

        props: {
            'autoscrollEnabled': {
                type: Boolean,
                default: true
            }
        },
        data: function () {
            return {
                atBottom: false,
                atTop: false,
                mouseDown: false,
                scrollUpdater: null,
                needScrollUpdate: false,
                linesCount: 0
            }
        },

        mounted: function () {
            this.recalculateScrollPosition();
            window.addEventListener('resize', this.revalidateScroll);

            this.scrollUpdater = window.setInterval(function () {
                if (!this.needScrollUpdate) {
                    return;
                }
                this.needScrollUpdate = false;

                var autoscrolled = false;
                if (this.autoscrollEnabled) {
                    autoscrolled = this.autoscroll();
                }

                if (!autoscrolled) {
                    this.recalculateScrollPosition();
                }
            }.bind(this), 40);
        },

        methods: {
            recalculateScrollPosition: function () {
                var logContent = this.$refs.logContent;

                var scrollTop = logContent.scrollTop;
                var newAtBottom = (scrollTop + logContent.clientHeight + 5) > (logContent.scrollHeight);
                var newAtTop = scrollTop === 0;

                // sometimes we can get scroll update (from incoming text) between autoscroll and this method
                if (!this.needScrollUpdate) {
                    this.atBottom = newAtBottom;
                    this.atTop = newAtTop;
                }
            },

            autoscroll: function () {
                var logContent = this.$refs.logContent;
                if ((this.atBottom) && (!this.mouseDown)) {
                    logContent.scrollTop = logContent.scrollHeight;
                    return true;
                }
                return false;
            },

            revalidateScroll: function () {
                this.needScrollUpdate = true;
            },

            setLog: function (text) {
                destroyChildren(this.$refs.logContent);

                this.appendLog(text);
            },

            appendLog: function (text, textColor, backgroundColor, textStyles) {
                if (isNull(text) || (text === '')) {
                    return;
                }

                var logElement = this.createLogElement(text, textColor, backgroundColor, textStyles);
                this.$refs.logContent.appendChild(logElement);

                this.revalidateScroll();
            },

            replaceLog: function (text, textColor, backgroundColor, textStyles, x, y) {
                this._updateLinesCache();

                var logContent = this.$refs.logContent;
                var firstMatchingElement = _findFirstElementAtLine(logContent, y);

                if (isNull(firstMatchingElement)) {
                    console.log('WARN! Could not find element for line ' + y);
                    this.appendLog(text, textColor, backgroundColor, textStyles);
                    return;
                }

                var replaceLinesCount = getLinesCount(text);

                var currentLines = _createLinesFromElements(y, replaceLinesCount, firstMatchingElement);
                _replaceInLines(x, text, currentLines);
                _appendNewLineCharacter(currentLines);
                _updateElementsFromLines(currentLines, logContent, function (text) {
                    return this.createLogElement(text, textColor, backgroundColor, textStyles);
                }.bind(this));

                this.revalidateScroll();
            },

            _updateLinesCache: function () {
                var logContent = this.$refs.logContent;

                var linesCount = 0;
                for (var i = 0; i < logContent.childNodes.length; i++) {
                    var child = logContent.childNodes[i];

                    if (isNull(child.linesCount)) {
                        child.linesCount = getLinesCount(getLogElementText(child));
                    }

                    child.firstLine = linesCount;
                    linesCount += child.linesCount;
                    child.lastLine = linesCount;
                }
            },

            createTextAndAnchorElements: function (text) {
                var textElements;
                if (urlRegex.test(text)) {
                    textElements = [];

                    var match;
                    var lastEnd = 0;
                    urlRegex.lastIndex = 0;
                    while ((match = urlRegex.exec(text)) !== null) {
                        if (match.index > lastEnd) {
                            var prevText = text.substring(lastEnd, match.index);
                            textElements.push(document.createTextNode(prevText));
                        }
                        var anchorElement = document.createElement('a');
                        anchorElement.href = match[0];
                        anchorElement.innerText = match[0];
                        textElements.push(anchorElement);

                        lastEnd = urlRegex.lastIndex;
                    }

                    if (lastEnd < (text.length - 1)) {
                        var endText = text.substring(lastEnd, text.length);
                        textElements.push(document.createTextNode(endText));
                    }

                } else {
                    textElements = [document.createTextNode(text)];
                }
                return textElements;
            },

            createLogElement: function (text, textColor, backgroundColor, textStyles) {
                var outputElement = null;

                var textElements = this.createTextAndAnchorElements(text);

                if (!isNull(textColor) || !isNull(backgroundColor) || !isNull(textStyles)) {
                    outputElement = document.createElement('span');
                    if (!isNull(textColor)) {
                        addClass(outputElement, 'text_color_' + textColor);
                    }
                    if (!isNull(backgroundColor)) {
                        addClass(outputElement, 'background_' + backgroundColor);
                    }

                    if (!isNull(textStyles)) {
                        for (var styleIndex = 0; styleIndex < textStyles.length; styleIndex++) {
                            addClass(outputElement, 'text_style_' + textStyles[styleIndex]);
                        }
                    }

                    textElements.forEach(outputElement.appendChild.bind(outputElement));

                } else {
                    if (textElements.length === 1) {
                        outputElement = textElements[0];
                    } else {
                        outputElement = document.createElement('span');
                        textElements.forEach(outputElement.appendChild.bind(outputElement));
                    }
                }

                return outputElement;
            }
        },
        beforeDestroy: function () {
            window.removeEventListener('resize', this.revalidateScroll);
            window.clearInterval(this.scrollUpdater);
        }
    });
}());