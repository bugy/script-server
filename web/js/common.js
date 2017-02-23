function loadScript(scriptPath) {
    var code = callHttp(scriptPath);

    window.eval(code);
}

function findNeighbour(element, tag) {
    var tagLower = tag.toLowerCase();

    var previous = element.previousSibling;
    while (!isNull(previous)) {
        if (previous.tagName.toLowerCase() == tagLower) {
            return previous;
        }

        previous = previous.previousSibling;
    }

    var next = element.nextSibling;
    while (!isNull(next)) {
        if (next.tagName.toLowerCase() == tagLower) {
            return next;
        }

        next = next.nextSibling;
    }

    return null;
}

function isEmptyString(value) {
    return isNull(value) || value.length == 0;
}

function isEmptyObject(obj) {
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

// TODO: replace this with new fetch api
function callHttp(url, object, method, asyncHandler) {
    method = method || "GET";

    var xhttp = new XMLHttpRequest();

    var async = !isNull(asyncHandler);
    if (async) {
        xhttp.onreadystatechange = asyncHandler;
    }

    xhttp.open(method, url, async);

    try {
        if (!isNull(object)) {
            xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhttp.send(JSON.stringify(object));
        } else {
            xhttp.send();
        }
    } catch (error) {
        throw new HttpRequestError(xhttp.status, error.message);
    }

    if (!async) {
        if (xhttp.status == 200) {
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

function HttpRequestError(code, message) {
    this.code = code;
    this.message = message;
    var lastPart = new Error().stack.match(/[^\s]+$/);
    this.stack = `${this.name} at ${lastPart}`;
}
HttpRequestError.prototype = Object.create(Error.prototype);
HttpRequestError.prototype.name = "HttpRequestError";
HttpRequestError.prototype.message = "";
HttpRequestError.prototype.code = -1;
HttpRequestError.prototype.constructor = HttpRequestError;

function isNull(object) {
    return ((typeof object) == 'undefined' || (object == null));
}

function destroyChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function hide(element) {
    element.style.display = "none";
}

function show(element, displayStyle) {
    displayStyle = displayStyle || "block";
    element.style.display = displayStyle;
}

