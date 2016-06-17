var selectedScript = null;
var scriptListeners = [];
var parameterControls = [];
var runningScriptExecutor = null;

function onLoad() {
    var response = callHttp("scripts/list");

    var scripts = JSON.parse(response);

    var scriptsListElement = document.getElementById("scripts");

    scripts.forEach(function (script) {
        var scriptElement = document.createElement("a");

        addClass(scriptElement, "collection-item");
        addClass(scriptElement, "waves-effect");
        addClass(scriptElement, "waves-teal");
        scriptElement.setAttribute("href", "#" + script);
        scriptElement.onclick = function (e) {
            if (runningScriptExecutor != null) {
                if (!runningScriptExecutor.isFinished()) {
                    var abort = confirm("Another script is running. Do you want to abort?");
                    if (abort == true) {
                        runningScriptExecutor.abort();
                    } else {
                        return false;
                    }
                }

                runningScriptExecutor = null;
            }

            selectScript(script);
        };

        scriptElement.innerText = script;

        scriptListeners.push(function (activeScript) {
            if (activeScript == script) {
                addClass(scriptElement, "active");
            } else {
                removeClass(scriptElement, "active");
            }
        });

        scriptsListElement.appendChild(scriptElement);
    });

    var contentPanel = document.getElementById("contentPanel");
    hide(contentPanel);

    scriptListeners.push(function (activeScript) {
        showScript(activeScript)
    });

    var hash = getHash();
    if ((hash != null) && (scripts.indexOf(hash) != -1)) {
        selectScript(hash);
    }

    initLogPanel();
    initExecuteButton();
    initStopButton();
}

function initLogPanel() {
    var logPanel = document.getElementById("logPanel");

    hide(logPanel);

    var wasBottom = true;
    logPanel.onscroll = function () {
        var isTop = logPanel.scrollTop == 0;
        var isBottom = (logPanel.scrollTop + logPanel.clientHeight + 5) > (logPanel.scrollHeight);

        var shadowTop = !isTop;
        var shadowBottom = !isBottom;

        if (shadowTop && shadowBottom) {
            addClass(logPanel, "shadow-top-bottom");
            removeClass(logPanel, "shadow-top");
            removeClass(logPanel, "shadow-bottom");
        } else if (shadowTop) {
            removeClass(logPanel, "shadow-top-bottom");
            addClass(logPanel, "shadow-top");
            removeClass(logPanel, "shadow-bottom");
        } else if (shadowBottom) {
            removeClass(logPanel, "shadow-top-bottom");
            removeClass(logPanel, "shadow-top");
            addClass(logPanel, "shadow-bottom");
        } else {
            removeClass(logPanel, "shadow-top-bottom");
            removeClass(logPanel, "shadow-top");
            removeClass(logPanel, "shadow-bottom");
        }

        wasBottom = isBottom;
    };

    var mouseDown = false;
    logPanel.onmousedown = function () {
        mouseDown = true;
    };

    logPanel.onmouseup = function () {
        mouseDown = false;
    };

    var updateScroll = function (mutations) {
        if ((wasBottom) && (!mouseDown)) {
            logPanel.scrollTop = logPanel.scrollHeight;
        } else {
            logPanel.onscroll();
        }
    };

    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
    var observer = new MutationObserver(updateScroll);

    window.addEventListener('resize', function (event) {
        updateScroll([]);
    });

    var config = {attributes: false, subtree: true, childList: true, characterData: true};
    observer.observe(logPanel, config);
}

function initStopButton() {
    var stopButton = document.getElementById("stopButton");

    stopButton.onclick = function () {
        if (runningScriptExecutor != null) {
            runningScriptExecutor.stop();
        }
    };
}

function initExecuteButton() {
    var executeButton = document.getElementById("executeButton");
    executeButton.onclick = function (e) {
        var logPanel = document.getElementById("logPanel");
        var inputPanel = document.getElementById("inputPanel");

        logPanel.innerText = "Calling the script...";
        show(logPanel, "block");

        var callParameters = [];
        parameterControls.forEach(function (control) {
            callParameters.push({
                name: control.getParameterName(),
                value: control.getValue()
            })
        });

        var callBody = {
            script: selectedScript,
            parameters: callParameters
        };

        try {
            var process_id = callHttp("scripts/execute", callBody, "POST");

            runningScriptExecutor = new ScriptController(process_id);

            var stopButton = document.getElementById("stopButton");
            setButtonEnabled(stopButton, true);
            setButtonEnabled(executeButton, false);

        } catch (error) {
            logPanel.innerText = error.message;
        }
    };
}

function hide(element) {
    element.style.display = "none";
}

function show(element, displayStyle) {
    displayStyle = displayStyle || "block";
    element.style.display = displayStyle;
}

function showScript(activeScript) {
    var contentPanel = document.getElementById("contentPanel");
    show(contentPanel, "flex");

    var info = callHttp("scripts/info?name=" + activeScript);

    var parsedInfo = JSON.parse(info);

    var scriptHeader = document.getElementById("scriptHeader");
    scriptHeader.innerText = parsedInfo.name;

    var scriptDescription = document.getElementById("scriptDescription");
    scriptDescription.innerText = parsedInfo.description;

    var paramsPanel = document.getElementById("parametersPanel");
    paramsPanel.innerHTML = "";

    parameterControls = [];
    if (!isNull(parsedInfo.parameters)) {
        parsedInfo.parameters.forEach(function (parameter) {
            var control = createParameterControl(parameter);
            parameterControls.push(control);
        });
    }

    if (parameterControls.length > 0) {
        show(paramsPanel, "block");

        parameterControls.forEach(function (control) {
            var element = control.getElement();
            addClass(element, "parameter");

            paramsPanel.appendChild(element);
        })
    } else {
        hide(paramsPanel);
    }


    var logPanel = document.getElementById("logPanel");
    hide(logPanel);
    logPanel.innerText = "";

    var inputPanel = document.getElementById("inputPanel");
    hide(inputPanel);

    var stopButton = document.getElementById("stopButton");
    var executeButton = document.getElementById("executeButton");

    setButtonEnabled(executeButton, true);
    setButtonEnabled(stopButton, false);
}

function createParameterControl(parameter) {
    var panel = document.createElement("div");
    addClass(panel, "input-field");

    var getValue = null;

    if (parameter.withoutValue) {
        var label = document.createElement("label");
        label.setAttribute("for", parameter.name);
        label.innerText = parameter.name;

        var checkBox = document.createElement("input");
        checkBox.id = parameter.name;
        checkBox.type = "checkbox";

        getValue = function () {
            return checkBox.checked;
        };

        panel.appendChild(checkBox);
        panel.appendChild(label);

    } else {
        var label = document.createElement("label");
        label.setAttribute("for", parameter.name);
        label.innerText = parameter.name;

        var field = document.createElement("input");
        field.id = parameter.name;
        field.type = "text";

        getValue = function () {
            return field.value;
        };

        panel.appendChild(field);
        panel.appendChild(label);
    }

    return new function () {
        this.getElement = function () {
            return panel;
        };

        this.getValue = getValue;

        this.getParameterName = function () {
            return parameter.name;
        }
    };
}


function selectScript(scriptName) {
    selectedScript = scriptName;

    scriptListeners.forEach(function (listener) {
        listener(selectedScript);
    })
}

function isNull(object) {
    return ((typeof object) == 'undefined' || (object == null));
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

function getHash() {
    if (location.hash == 'undefined') {
        return null;
    }

    if (location.hash.length <= 1) {
        return null;
    }

    return decodeURIComponent(location.hash.substr(1));
}

function removeClass(element, clazz) {
    var className = element.className;
    className = className.replace(new RegExp("(\\s+|^)" + clazz + "(\\s+|$)"), " ");
    element.className = className;
}

function addClass(element, clazz) {
    var className = element.className;
    if (className.search("(\\s|^)" + clazz + "(\\s|$)") >= 0) {
        return;
    }

    if (!className.endsWith(" ")) {
        className += " ";
    }
    className += clazz;

    element.className = className;
}

function setButtonEnabled(button, enabled) {
    button.disabled = !enabled;
    if (!enabled) {
        addClass(button, "disabled");
    } else {
        removeClass(button, "disabled");
    }
}

function ScriptController(processId) {
    this.processId = processId;

    var inputPanel = document.getElementById("inputPanel");
    var executeButton = document.getElementById("executeButton");
    var stopButton = document.getElementById("stopButton");

    var ws = new WebSocket("ws://" + window.location.host + "/scripts/execute/io/" + processId);

    var receivedData = false;
    var logPanel = document.getElementById("logPanel");

    ws.onmessage = function (message) {
        if (!receivedData) {
            logPanel.innerText = "";
            receivedData = true;
        }

        var events = message.data.split(/(?={)/);

        events.forEach(function (event) {
            if (event.trim().length == 0) {
                return
            }

            var response = JSON.parse(event);

            var eventType = response.event;
            var data = response.data;

            if (eventType == "output") {
                var textNode = document.createTextNode(data);
                logPanel.appendChild(textNode);
                return;
            }

            if (eventType == "input") {
                var inputLabel = document.getElementById("inputLabel");
                inputLabel.innerText = data;

                var inputField = document.getElementById("inputField");
                inputField.value = "";

                inputField.onkeyup = function (event) {
                    if (event.keyCode == 13) {
                        ws.send(inputField.value);

                        inputField.value = "";
                    }
                };

                show(inputPanel, "block");
                inputField.focus();
            }
        });
    };

    ws.onclose = function (event) {
        setButtonEnabled(stopButton, false);
        setButtonEnabled(executeButton, true);
        runningScriptExecutor = null;

        hide(inputPanel);
    };

    this.stop = function () {
        callHttp("scripts/execute/stop", {"processId": this.processId}, "POST");
    };

    this.abort = function () {
        this.stop();

        if (!this.isFinished()) {
            ws.close();
        }
    };

    this.isFinished = function () {
        return ((ws.readyState == 2) && (ws.readyState == 3));
    };
}