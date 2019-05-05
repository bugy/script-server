import {destroyChildren, isNull} from '../../common';

const lineElementTemplate = document.createElement('div');

const urlRegex = new RegExp('https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{2,256}(\\.[a-z]{2,6})?(:\\d{2,6})?' +
    '(\\.*([-a-zA-Z0-9@:%_\\+~#?//=])+&?)*',
    'g');


export class Terminal {
    constructor(terminalModel) {
        this.element = document.createElement('code');
        this.terminalModel = terminalModel;

        terminalModel.addListener(this);
    }

    static createLineElement() {
        return lineElementTemplate.cloneNode();
    }

    static createTextAndAnchorElements(text) {
        const textElements = [];
        if (urlRegex.test(text)) {
            let match;
            let lastEnd = 0;
            urlRegex.lastIndex = 0;
            while ((match = urlRegex.exec(text)) !== null) {
                if (match.index > lastEnd) {
                    const prevText = text.substring(lastEnd, match.index);
                    textElements.push(document.createTextNode(prevText));
                }
                const anchorElement = document.createElement('a');
                anchorElement.href = match[0];
                anchorElement.innerText = match[0];
                textElements.push(anchorElement);

                lastEnd = urlRegex.lastIndex;
            }

            if (lastEnd < text.length) {
                const endText = text.substring(lastEnd, text.length);
                textElements.push(document.createTextNode(endText));
            }

        } else {
            textElements.push(document.createTextNode(text));
        }
        return textElements;
    }

    static createLogLineChildren(lineText, styleRanges) {
        if (isNull(styleRanges)) {
            return Terminal.createTextAndAnchorElements(lineText);
        }

        let lastIndex = 0;

        const result = [];
        for (const styleRange of styleRanges) {
            if (styleRange.start > lastIndex) {
                const prevText = lineText.substr(lastIndex, styleRange.start - lastIndex);
                const nonStyledElements = Terminal.createStyledElements(prevText);
                result.push(...nonStyledElements);
            }

            if (isNull(styleRange.style) || styleRange.style.isEmpty()) {
                continue;
            }

            const subtext = lineText.substr(styleRange.start, styleRange.end - styleRange.start);
            const styledElements = Terminal.createStyledElements(
                subtext,
                styleRange.style.color,
                styleRange.style.background,
                styleRange.style.styles);
            result.push(...styledElements);

            lastIndex = styleRange.end;
        }

        if (lastIndex < lineText.length) {
            const nonStyledElements = Terminal.createStyledElements(lineText.substr(lastIndex));
            result.push(...nonStyledElements);
        }

        return result;
    }

    static createStyledElements(text, textColor, backgroundColor, textStyles) {
        const textElements = Terminal.createTextAndAnchorElements(text);

        if (!isNull(textColor) || !isNull(backgroundColor) || !isNull(textStyles)) {
            const outputElement = document.createElement('span');

            let className = '';

            if (!isNull(textColor)) {
                className += ' text_color_' + textColor;
            }
            if (!isNull(backgroundColor)) {
                className += ' background_' + backgroundColor;
            }

            if (!isNull(textStyles)) {
                for (let styleIndex = 0; styleIndex < textStyles.length; styleIndex++) {
                    className += ' text_style_' + textStyles[styleIndex];
                }
            }

            outputElement.className = className;
            textElements.forEach(outputElement.appendChild.bind(outputElement));
            return [outputElement];

        }

        return textElements;
    }

    linesChanges(changedLines) {
        const terminalModel = this.terminalModel;
        if (changedLines.length === 0) {
            return;
        }

        const modelLines = terminalModel.lines;

        const parentElement = this.element;

        const oldLinesCounts = parentElement.childElementCount;

        const replacedLines = new Map();

        const newLinesFragment = document.createDocumentFragment();

        const lastIndex = changedLines[changedLines.length - 1];
        for (let i = oldLinesCounts; i <= lastIndex; i++) {
            const lineElement = Terminal.createLineElement();
            newLinesFragment.appendChild(lineElement);
        }

        for (const lineIndex of changedLines) {
            let lineElement;

            if (lineIndex >= oldLinesCounts) {
                lineElement = newLinesFragment.children[lineIndex - oldLinesCounts];
            } else {
                lineElement = Terminal.createLineElement();
                replacedLines.set(lineIndex, lineElement);
            }

            const lineText = modelLines[lineIndex];
            const styleRanges = terminalModel.getStyle(lineIndex);

            const children = Terminal.createLogLineChildren(lineText, styleRanges);
            children.forEach(child => lineElement.appendChild(child));
        }

        for (const child of newLinesFragment.children) {
            if (child.firstChild === null) {
                newLinesFragment.replaceChild(document.createElement('br'), child);
            }
        }

        replacedLines.forEach((value, key) => {
            parentElement.replaceChild(value, parentElement.children[key]);
        });
        parentElement.appendChild(newLinesFragment);
    }

    cleared() {
        destroyChildren(this.element);
    }

    linesDeleted(startLine, endLine) {
        if (startLine >= this.element.childElementCount) {
            return;
        }

        const lastIndex = Math.min(endLine - 1, this.element.childElementCount - 1);
        for (let i = lastIndex; i >= startLine; i--) {
            const childNode = this.element.childNodes[i];
            this.element.removeChild(childNode);
        }
    }
}
