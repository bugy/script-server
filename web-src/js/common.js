function loadScript(url) {
    var script = document.createElement('script');
    script.src = url;
    script.async = false;
    document.head.appendChild(script);
}

function findNeighbour(element, tag) {
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

function isEmptyString(value) {
    return isNull(value) || value.length === 0;
}

function isEmptyArray(value) {
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

function isEmptyObject(obj) {
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

function addClass(element, clazz) {
    if (!hasClass(element, clazz)) {
        element.classList.add(clazz);
    }
}

function hasClass(element, clazz) {
    return element.classList.contains(clazz);
}

function removeClass(element, clazz) {
    element.classList.remove(clazz);
}

function callHttp(url, object, method, asyncHandler, onError) {
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

var HttpRequestError = _createErrorType('HttpRequestError', function (code, message) {
    this.code = code || -1;
    this.message = message || '';
});

var SocketClosedError = _createErrorType('SocketClosedError', function (code, reason) {
    this.code = code || -1;
    this.reason = reason || '';
});

var HttpUnauthorizedError = _createErrorType('HttpUnauthorizedError', function (code, message) {
    this.code = code || -1;
    this.message = message || '';
});

function isNull(object) {
    return ((typeof object) === 'undefined' || (object === null));
}

function destroyChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function hide(element) {
    var currentDisplay = window.getComputedStyle(element).display;
    if (currentDisplay === 'none') {
        return;
    }

    element.oldDisplay = currentDisplay;
    element.style.display = 'none';
}

function show(element, displayStyle) {
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

function removeElement(array, element) {
    var index = array.indexOf(element);
    if (index >= 0) {
        array.splice(index, 1);
    }

    return array;
}

function removeElements(array, elements) {
    for (var i = 0; i < elements.length; i++) {
        var element = elements[i];
        removeElement(array, element);
    }
}

function clearArray(array) {
    array.splice(0, array.length);
}

function guid(length) {
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

function logError(error) {
    (console.error || console.log).call(console, error.stack || error);
}

function createTemplateElement(templateName) {
    var template = $('#' + templateName).html().trim();
    var element = $.parseHTML(template)[0];

    var clazz = templateName.replace(/-template$/g, '');
    addClass(element, clazz);

    return element;
}

function bindTemplatedFieldLabel(field, label) {
    field.id = 'script-input-field-' + guid(8);
    label.for = field.id;
}

function readQueryParameters() {
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

function getQueryParameter(parameter, url) {
    var parameters = readQueryParameters(url);
    return parameters[parameter];
}

function getUrlDir() {
    var path = window.location.pathname;
    return path.substring(0, path.lastIndexOf('/'));
}

function getWebsocketUrl(relativePath) {
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

function isWebsocketClosed(websocket) {
    return ((websocket.readyState === 2) || (websocket.readyState === 3));
}

function getUnparameterizedUrl() {
    return [location.protocol, '//', location.host, location.pathname].join('');
}

function contains(array, element) {
    return array.indexOf(element) !== -1
}

function forEachKeyValue(array, callback) {
    for (var key in array) {
        if (array.hasOwnProperty(key)) {
            var value = array[key];
            callback(key, value);
        }
    }
}

function toBoolean(value) {
    if (typeof(value) === 'boolean') {
        return value;

    } else if (typeof(value) === 'string') {
        return value.toLowerCase() === 'true';

    } else {
        return Boolean(value);
    }
}

function getLinesCount(text) {
    var linesMatch = text.match(/\n/g);
    return isNull(linesMatch) ? 0 : linesMatch.length;
}

function arraysEqual(arr1, arr2) {
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

function setInputValue(inputField, value, triggerEvent) {
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

function toDict(array, fieldName) {
    var result = {};
    for (var i = 0; i < array.length; i++) {
        var element = array[i];
        result[element[fieldName]] = element;
    }
    return result;
}