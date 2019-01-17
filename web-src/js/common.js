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
    return isNull(value) || value.length === 0;
}

export function isEmptyArray(value) {
    return isNull(value) || value.length === 0;
}

function isEmptyValue(value) {
    if (isNull(value)) {
        return true;
    }

    if ((typeof value === 'string') || (Array.isArray(value))) {
        return value.length === 0;
    }

    if (typeof value === 'object') {
        return isEmptyObject(value);
    }
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
    return element.classList.contains(clazz);
}

export function removeClass(element, clazz) {
    element.classList.remove(clazz);
}

export function callHttp(url, object, method, asyncHandler, onError) {
    method = method || "GET";

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
                console.log('Failed to execute request: ' + event);
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
            var message = "Couldn't execute request.";
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

export function hide(element) {
    var currentDisplay = window.getComputedStyle(element).display;
    if (currentDisplay === 'none') {
        return;
    }

    element.oldDisplay = currentDisplay;
    element.style.display = 'none';
}

export function show(element, displayStyle) {
    if (isNull(displayStyle) && (isNull(element.oldDisplay))) {
        if (element.style.display === 'none') {
            element.style.display = '';
        }

        var currentDisplay = window.getComputedStyle(element).display;
        if (currentDisplay !== 'none') {
            return;
        }
    }

    displayStyle = displayStyle || element.oldDisplay || 'block';
    element.style.display = displayStyle;
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
    var template = $('#' + templateName).html().trim();
    var element = $.parseHTML(template)[0];

    var clazz = templateName.replace(/-template$/g, '');
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
        hostUrl += '/' + dir;
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
    if (typeof(value) === 'boolean') {
        return value;

    } else if (typeof(value) === 'string') {
        return value.toLowerCase() === 'true';

    } else {
        return Boolean(value);
    }
}

export function getLinesCount(text) {
    var linesMatch = text.match(/\n/g);
    return isNull(linesMatch) ? 0 : linesMatch.length;
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

    if (inputField instanceof jQuery) {
        inputField = inputField.get(0);
    }

    inputField.value = value;

    if (triggerEvent) {
        var event = document.createEvent('HTMLEvents');
        event.initEvent('input', true, true);
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

export function setButtonEnabled(button, enabled) {
    button.disabled = !enabled;
    if (!enabled) {
        addClass(button, "disabled");
    } else {
        removeClass(button, "disabled");
    }
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