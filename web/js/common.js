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
    if (hasClass(element, clazz)) {
        return;
    }

    var className = element.className;

    if (!className.endsWith(" ")) {
        className += " ";
    }
    className += clazz;

    element.className = className;
}

function hasClass(element, clazz) {
    return element.className.search("(\\s|^)" + clazz + "(\\s|$)") >= 0;
}

function removeClass(element, clazz) {
    var className = element.className;
    className = className.replace(new RegExp("(\\s+|^)" + clazz + "(\\s+|$)"), " ");
    element.className = className;
}

function callHttp(url, object, method, asyncHandler) {
    method = method || "GET";

    var xhttp = new XMLHttpRequest();

    var async = !isNull(asyncHandler);
    if (async) {
        xhttp.onreadystatechange = asyncHandler;
    }

    xhttp.open(method, url, async);

    if (!isNull(object)) {
        xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhttp.send(JSON.stringify(object));
    } else {
        xhttp.send();
    }

    if (!async) {
        if (xhttp.status == 200) {
            return xhttp.responseText;

        } else {
            var message = "Couldn't execute request.";
            if (!isNull(xhttp.responseText) && (xhttp.responseText.length > 0)) {
                message = xhttp.responseText;
            }
            throw new Error(message);
        }
    } else {
        return xhttp;
    }
}

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