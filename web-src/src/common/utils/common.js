export function findNeighbour(element, tag) {
    var tagLower = tag.toLowerCase();

    var previous = element.previousSibling;
    while (!isNull(previous)) {
        if (previous.tagName.toLowerCase() === tagLower) {
            return previous;
        }

        previous = previous.previousSibling;
    }

    var next = element.nextSibling;
    while (!isNull(next)) {
        if (next.tagName.toLowerCase() === tagLower) {
            return next;
        }

        next = next.nextSibling;
    }

    return null;
}

export function isEmptyString(value) {
    return isNull(value) || ((typeof value === 'string') && (value.length === 0));
}

export function isBlankString(value) {
    return isNull(value) || ((typeof value === 'string') && (value.trim().length === 0));
}

export function isEmptyArray(value) {
    return isNull(value) || value.length === 0;
}

export function isEmptyValue(value) {
    if (isNull(value)) {
        return true;
    }

    if ((typeof value === 'string') || (Array.isArray(value))) {
        return value.length === 0;
    }

    if (typeof value === 'object') {
        return isEmptyObject(value);
    }

    return false;
}

export function isEmptyObject(obj) {
    if (isNull(obj)) {
        return true;
    }

    for (var prop in obj) {
        if (obj.hasOwnProperty(prop)) {
            return false;
        }
    }

    return true;
}

export function addClass(element, clazz) {
    if (!hasClass(element, clazz)) {
        element.classList.add(clazz);
    }
}

export function hasClass(element, clazz) {
    if (isNull(element.classList)) {
        return false;
    }

    return element.classList.contains(clazz);
}

export function removeClass(element, clazz) {
    element.classList.remove(clazz);
}

export function callHttp(url, object, method, asyncHandler, onError) {
    method = method || 'GET';

    var xhttp = new XMLHttpRequest();

    var async = !isNull(asyncHandler);
    if (async) {
        xhttp.onreadystatechange = function () {
            if (xhttp.readyState === XMLHttpRequest.DONE) {
                if (xhttp.status === 200) {
                    asyncHandler(xhttp.responseText);
                } else if (onError) {
                    onError(xhttp.status, xhttp.responseText);
                }
            }
        };

        if (onError) {
            xhttp.addEventListener('error', function (event) {
                console.log('Failed to execute request');
                console.log(event);
                onError(-1, 'Unknown error occurred');
            });
        }
    }

    xhttp.open(method, url, async);
    xhttp.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    try {
        if (object instanceof FormData) {
            xhttp.send(object);

        } else if (!isNull(object)) {
            xhttp.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
            xhttp.send(JSON.stringify(object));

        } else {
            xhttp.send();
        }
    } catch (error) {
        throw new HttpRequestError(xhttp.status, error.message);
    }

    if (!async) {
        if (xhttp.status === 200) {
            return xhttp.responseText;

        } else {
            var message = 'Couldn\'t execute request.';
            if (!isNull(xhttp.responseText) && (xhttp.responseText.length > 0)) {
                message = xhttp.responseText;
            }
            throw new HttpRequestError(xhttp.status, message);
        }
    } else {
        return xhttp;
    }
}

function _createErrorType(name, init) {
    function NewErrorType(code, message) {
        if (!Error.captureStackTrace) {
            this.stack = (new Error()).stack;
        } else {
            Error.captureStackTrace(this, this.constructor);
        }
        if (arguments['message']) {
            this.message = arguments['message'];
        }

        if (init) {
            init.apply(this, arguments);
        }
    }

    NewErrorType.prototype = Object.create(Error.prototype);
    NewErrorType.prototype.name = name;
    NewErrorType.prototype.constructor = NewErrorType;
    return NewErrorType;
}

export const HttpRequestError = _createErrorType('HttpRequestError', function (code, message) {
    this.code = code || -1;
    this.message = message || '';
});

export const SocketClosedError = _createErrorType('SocketClosedError', function (code, reason) {
    this.code = code || -1;
    this.reason = reason || '';
});

export const HttpForbiddenError = _createErrorType('HttpForbiddenError', function (code, message) {
    this.code = code || -1;
    this.message = message || '';
});

export const HttpUnauthorizedError = _createErrorType('HttpUnauthorizedError', function (code, message) {
    this.code = code || -1;
    this.message = message || '';
});

export function isNull(object) {
    return ((typeof object) === 'undefined' || (object === null));
}

export function destroyChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

export function removeElement(array, element) {
    var index = array.indexOf(element);
    if (index >= 0) {
        array.splice(index, 1);
    }

    return array;
}

// removes elements from the array, for which predicate is true
export function removeElementIf(array, predicate) {
    for (let i = array.length; i >= 0; i--) {
        const arrayElement = array[i];
        if (predicate(arrayElement)) {
            array.splice(i, 1);
        }
    }
}

export function removeElements(array, elements) {
    for (var i = 0; i < elements.length; i++) {
        var element = elements[i];
        removeElement(array, element);
    }
}

export function clearArray(array) {
    array.splice(0, array.length);
}

export function guid(length) {
    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
    }

    var guid = s4() + s4() + '-' + s4() + '-' + s4() + '-' +
        s4() + '-' + s4() + s4() + s4();


    if (length && length > 0) {
        if (guid.length < length) {
            while (guid.length < length) {
                guid += guid;
            }
        }

        if (guid.length > length) {
            guid = guid.substring(0, length);
        }
    }

    return guid;
}

export function logError(error) {
    (console.error || console.log).call(console, error.stack || error);
}

export function createTemplateElement(templateName) {
    const templateContent = document.getElementById(templateName).innerHTML.trim();

    const template = document.createElement('template');
    template.innerHTML = templateContent;
    const element = template.content.childNodes[0];

    const clazz = templateName.replace(/-template$/g, '');
    addClass(element, clazz);

    return element;
}

export function readQueryParameters() {
    var argString = window.location.search;
    if (!argString || argString.length <= 1) {
        return {};
    }

    var pairs = argString.substr(1).split('&');

    var result = {};
    for (var i = 0; i < pairs.length; i++) {
        var keyAndValue = pairs[i].split('=', 2);

        if (keyAndValue.length !== 2) {
            continue;
        }

        var key = decodeURIComponent(keyAndValue[0].replace(/\+/g, ' '));
        var value = decodeURIComponent(keyAndValue[1].replace(/\+/g, ' '));

        result[key] = value;
    }

    return result;
}

export function getQueryParameter(parameter, url) {
    var parameters = readQueryParameters(url);
    return parameters[parameter];
}

function getUrlDir() {
    var path = window.location.pathname;
    return path.substring(0, path.lastIndexOf('/'));
}

export function getWebsocketUrl(relativePath) {
    var location = window.location;

    var https = location.protocol.toLowerCase() === 'https:';
    var wsProtocol = https ? 'wss' : 'ws';
    var hostUrl = wsProtocol + '://' + location.host;

    var dir = getUrlDir();
    if (dir) {
        hostUrl += dir;
    }

    if (isEmptyString(relativePath)) {
        return hostUrl;
    }

    if (!hostUrl.endsWith('/')) {
        hostUrl += '/';
    }

    return hostUrl + relativePath;
}

export function isWebsocketClosed(websocket) {
    return ((websocket.readyState === 2) || (websocket.readyState === 3));
}

export function isWebsocketConnecting(websocket) {
    return (websocket.readyState === 0)
}

export function isWebsocketOpen(websocket) {
    return !isNull(websocket) && (websocket.readyState === 1);
}

export function getUnparameterizedUrl() {
    return [location.protocol, '//', location.host, location.pathname].join('');
}

export function contains(array, element) {
    return array.indexOf(element) !== -1
}

export function forEachKeyValue(array, callback) {
    for (var key in array) {
        if (array.hasOwnProperty(key)) {
            var value = array[key];
            callback(key, value);
        }
    }
}

export function toBoolean(value) {
    if (typeof (value) === 'boolean') {
        return value;

    } else if (typeof (value) === 'string') {
        return value.toLowerCase() === 'true';

    } else {
        return Boolean(value);
    }
}

export function arraysEqual(arr1, arr2) {
    if (arr1 === arr2) {
        return true;
    }
    if (isNull(arr1) && (isNull(arr2))) {
        return true;
    }
    if (isNull(arr1) !== (isNull(arr2))) {
        return false;
    }
    if (arr1.length !== arr2.length) {
        return false;
    }

    for (var i = 0; i < arr1.length; ++i) {
        if (arr1[i] !== arr2[i]) {
            return false;
        }
    }

    return true;
}

export function setInputValue(inputField, value, triggerEvent) {
    if (isNull(triggerEvent)) {
        triggerEvent = false;
    }

    if (inputField.type === 'checkbox') {
        inputField.checked = value;
        inputField.indeterminate = isNull(value)
    } else {
        inputField.value = value;
    }

    if (triggerEvent) {
        const event = document.createEvent('HTMLEvents');
        let eventType = 'input';
        if (inputField.tagName === 'SELECT') {
            eventType = 'change';
        }
        event.initEvent(eventType, true, true);
        inputField.dispatchEvent(event);
    }
}

if (!String.prototype.endsWith) {
    String.prototype.endsWith = function (search, this_len) {
        if (this_len === undefined || this_len > this.length) {
            this_len = this.length;
        }
        return this.substring(this_len - search.length, this_len) === search;
    };
}

export function toDict(array, fieldName) {
    var result = {};
    for (var i = 0; i < array.length; i++) {
        var element = array[i];
        result[element[fieldName]] = element;
    }
    return result;
}

function compareNulls(value1, value2) {
    if (isNull(value1) && isNull(value2)) {
        return 0;
    }

    if (isNull(value1)) {
        return -1;
    } else if (isNull(value2)) {
        return 1;
    }

    return null;
}

export function stringComparator(field) {
    const comparator = function (a, b) {
        const objectNullComparison = compareNulls(a, b);
        if (!isNull(objectNullComparison)) {
            return objectNullComparison;
        }

        const value1 = a[field];
        const value2 = b[field];

        const valueNullComparison = compareNulls(a, b);
        if (!isNull(valueNullComparison)) {
            return valueNullComparison;
        }

        return value1.toLowerCase().localeCompare(value2.toLowerCase());
    };

    comparator.andThen = function (anotherComparator) {
        return function (a, b) {
            const result = comparator(a, b);
            if (result !== 0) {
                return result;
            }

            return anotherComparator(a, b);
        }
    };

    return comparator
}

export function scrollToElement(element, onlyWhenOutside = false) {
    if (onlyWhenOutside && isVisibleOnScroll(element, false)) {
        return;
    }

    const scrollableParent = findScrollableParent(element);
    let alignToTop;
    if (isNull(scrollableParent)) {
        alignToTop = true;
    } else {
        alignToTop = element.offsetTop < scrollableParent.scrollTop;
    }

    element.scrollIntoView(alignToTop);
}

function findScrollableParent(elem) {
    let scrollableParent = elem.parentNode;
    while (!isNull(scrollableParent)) {
        if (scrollableParent.scrollHeight > scrollableParent.clientHeight) {
            return scrollableParent;
        }

        scrollableParent = scrollableParent.parentNode;
    }

    return scrollableParent;
}

function isVisibleOnScroll(elem, partially = true) {
    let scrollableParent = findScrollableParent(elem);

    if (!scrollableParent) {
        return false;
    }

    const scrollTop = scrollableParent.scrollTop;
    const scrollBottom = scrollTop + scrollableParent.clientHeight;

    const elemTop = elem.offsetTop;
    const elemBottom = elemTop + elem.clientHeight;

    if (partially) {
        return (elemBottom > scrollTop) && (elemTop < scrollBottom);
    } else {
        return (elemTop >= scrollTop) && (elemBottom <= scrollBottom);
    }
}

export function getTextWidth(text, element) {
    // re-use canvas object for better performance
    const canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement('canvas'));

    const context = canvas.getContext('2d');
    context.font = window.getComputedStyle(element, null).getPropertyValue('font');
    const metrics = context.measureText(text);
    return metrics.width;
}

export function toMap(elements, keyExtractor, valueExtractor) {
    return elements.reduce(
        (obj, element) =>
            Object.assign(obj, {[keyExtractor(element)]: valueExtractor(element)})
        , {}
    );
}

export function deepCloneObject(obj) {
    return JSON.parse(JSON.stringify(obj));
}

// Reads the text, which user sees
// Default innerText doesn't work (on Chrome/Firefox), because <br/> is treated as double new-line
// So the idea is just select text and copy it
function readUserVisibleText(elem) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(elem);
    selection.removeAllRanges();
    selection.addRange(range);
    const selectionString = selection.toString();
    selection.removeAllRanges();
    return selectionString;
}

export function copyToClipboard(elem) {
    // if new Clipboard API is available, just use it
    if (navigator.clipboard) {
        const selectionString = readUserVisibleText(elem);
        navigator.clipboard.writeText(selectionString);
        return;
    }

    const targetId = '_hiddenCopyText_';
    const isInput = elem.tagName === 'INPUT' || elem.tagName === 'TEXTAREA';

    let origSelectionStart, origSelectionEnd;
    let target;
    if (isInput) {
        target = elem;
        origSelectionStart = elem.selectionStart;
        origSelectionEnd = elem.selectionEnd;
    } else {
        target = document.getElementById(targetId);
        if (!target) {
            target = document.createElement('textarea');
            target.style.position = 'absolute';
            target.style.left = '9999px';
            target.style.top = '0';
            target.id = targetId;
            document.body.appendChild(target);
        }
        target.value = readUserVisibleText(elem);
    }

    const currentFocus = document.activeElement;
    target.focus();
    target.setSelectionRange(0, target.value.length);

    try {
        document.execCommand('copy');
    } catch (e) {
        console.error(e);
    }

    if (currentFocus && typeof currentFocus.focus === 'function') {
        currentFocus.focus();
    }

    if (isInput) {
        elem.setSelectionRange(origSelectionStart, origSelectionEnd);
    } else {
        target.textContent = '';
    }

    document.body.removeChild(target);

    // for mobiles, we need to scroll down to make URL bar disappear
    elem.scrollIntoView();
}

export function uuidv4() {
    return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

export function closestByClass(element, className) {
    if (className.startsWith('.')) {
        className = className.substring(0, className.length - 1);
    }

    let current = element;
    while (current != null) {
        if (hasClass(current, className)) {
            return current;
        }
        current = current.parentNode;
    }

    return current;
}

export function toQueryArgs(obj) {
    const searchParams = new URLSearchParams();
    forEachKeyValue(obj, (key, value) => {
        if (Array.isArray(value)) {
            for (const arrayElement of value) {
                searchParams.append(key, arrayElement);
            }
        } else {
            searchParams.append(key, value);
        }
    });
    return searchParams.toString()
}

export function randomInt(start, end) {
    if (start > end) {
        start++;
        end++;
    } else if (end === start) {
        return start;
    }

    const random = Math.random() * (end - start);
    return Math.floor(random) + start
}

export function trimTextNodes(el) {
    for (let node of el.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            node.data = node.data.trim();
        }
    }
}

export function getElementsByTagNameRecursive(parent, tag) {
    const tagLower = tag.toLowerCase();

    const result = [];

    const queue = [];
    queue.push(...parent.childNodes);

    while (!isEmptyArray(queue)) {
        const next = queue.shift()

        if (next.tagName && (next.tagName.toLowerCase() === tagLower)) {
            result.push(next);
        }

        queue.push(...next.childNodes);
    }

    return result;
}

export function getFileInputValue(fileField) {
    const files = fileField.files;
    let value;
    if (files && (files.length > 0)) {
        value = files[0];
    } else {
        value = null;
    }

    return value
}

export function isFullRegexMatch(regex, value) {
    let fullStringPattern = regex

    if (!fullStringPattern.startsWith('^')) {
        fullStringPattern = '^' + fullStringPattern
    }

    if (!fullStringPattern.endsWith('$')) {
        fullStringPattern += '$'
    }

    const regexPattern = new RegExp(fullStringPattern)
    return regexPattern.test(value)
}