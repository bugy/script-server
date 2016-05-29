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
    logPanel.onscroll = function () {
        var shadowTop = (logPanel.scrollTop > 0);
        var shadowBottom = (logPanel.scrollTop + logPanel.clientHeight) < (logPanel.scrollHeight - 1);

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
    };
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
        logPanel.style.display = "block";

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

        var stopButton = document.getElementById("stopButton");

        setButtonEnabled(stopButton, true);
        setButtonEnabled(executeButton, false);

        runningScriptExecutor = new ScriptExecutor();

        var httpRequest = callHttp("scripts/execute", callBody, "POST", runningScriptExecutor.processScriptResponse);
        runningScriptExecutor.setHttpRequest(httpRequest);
    };
}

function hide(element) {
    element.style.display = "none";
}

function showScript(activeScript) {
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
        paramsPanel.style.display = "block";

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
        return xhttp.responseText;
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

    return location.hash.substr(1);
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

function wrapInDiv(element, divClasses) {
    var logDiv = document.createElement("div");

    addClass(logDiv, divClasses);

    logDiv.appendChild(element);
    return logDiv;
}

function setButtonEnabled(button, enabled) {
    button.disabled = !enabled;
    if (!enabled) {
        addClass(button, "disabled");
    } else {
        removeClass(button, "disabled");
    }
}

function ScriptExecutor() {
    this.processId = null;
    this.httpRequest = null;
    this.availableResponseText = null;

    this.setHttpRequest = function (httpRequest) {
        this.httpRequest = httpRequest;
    };

    this.stop = function () {
        if (isNull(this.processId)) {
            throw "Cannot stop yet. Process id is not available";
        }

        callHttp("scripts/execute/stop", this.processId, "POST");
    };

    this.abort = function () {
        if (!isNull(this.httpRequest)) {
            this.httpRequest.abort()
        }
    };

    this.isFinished = function () {
        return !isNull(this.httpRequest) && (this.httpRequest.readyState == 4);
    };

    this.setProcessId = function (processId) {
        this.processId = processId;
    };

    this.getProcessId = function () {
        return this.processId;
    };

    var executor = this;

    this.processScriptResponse = function (event) {
        if (executor.httpRequest == null) {
            executor.httpRequest = event.currentTarget;
        }

        if ((executor.httpRequest.readyState == 4) || (executor.httpRequest.readyState == 3)) {
            if (executor.availableResponseText == null) {
                logPanel.innerText = "";
                executor.availableResponseText = "";
            }

            var newText = executor.httpRequest.responseText.substring(executor.availableResponseText.length);
            executor.availableResponseText = executor.httpRequest.responseText;

            var responses = newText.split(/(?={)/);
            responses.forEach(function (responseText) {
                if (responseText.trim().length == 0) {
                    return
                }

                var response = JSON.parse(responseText);

                if (response.hasOwnProperty("processId")) {
                    executor.setProcessId(response.processId);
                    return;
                }

                if (response.hasOwnProperty("output")) {
                    logPanel.innerText += response.output;
                    logPanel.onscroll();
                    return;
                }

                if (response.hasOwnProperty("input")) {
                    var inputLabel = document.getElementById("inputLabel");
                    inputLabel.innerText = response.input;

                    var inputField = document.getElementById("inputField");
                    inputField.value = "";

                    inputField.onkeyup = function (event) {
                        if (event.keyCode == 13) {
                            callHttp("scripts/execute/input", {
                                processId: executor.getProcessId(),
                                value: inputField.value
                            }, "POST");

                            inputField.value = "";
                        }
                    };

                    inputPanel.style.display = "block";
                    inputField.focus();
                }
            });
        }

        if (executor.httpRequest.readyState == 4) {
            setButtonEnabled(stopButton, false);
            setButtonEnabled(executeButton, true);
            runningScriptExecutor = null;

            hide(inputPanel);
        }
    }
}