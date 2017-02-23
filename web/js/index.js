loadScript("js/components/component.js");
loadScript("js/components/abstract_input.js");
loadScript("js/components/checkbox.js");
loadScript("js/components/textfield.js");
loadScript("js/components/combobox.js");


var selectedScript = null;
var scriptListeners = [];
var parameterControls;
var runningScriptExecutor = null;

function onLoad() {
    // TODO: replace this with Map 
    parameterControls = new Hashtable();

    var response = authorizedCallHttp("scripts/list");

    var scripts = JSON.parse(response);

    var scriptsListElement = document.getElementById("scripts");

    scripts.sort(function (name1, name2) {
        return name1.toLowerCase().localeCompare(name2.toLowerCase());
    });

    var scriptHashes = new Hashtable();

    scripts.forEach(function (script) {
        var scriptElement = document.createElement("a");

        var scriptHash = script.replace(/\s/g, "_");
        scriptHashes.put(scriptHash, script);

        addClass(scriptElement, "collection-item");
        addClass(scriptElement, "waves-effect");
        addClass(scriptElement, "waves-teal");
        scriptElement.setAttribute("href", "#" + scriptHash);
        scriptElement.addEventListener("click", function (e) {
            if (!stopRunningScript()) {
                return;
            }

            selectScript(script);
        });

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
    if (!isNull(hash)) {
        var scriptName = scriptHashes.get(hash);
        if (isNull(scriptName)) {
            scriptName = hash;
        }

        if (scripts.indexOf(scriptName) != -1) {
            selectScript(scriptName);
        }
    }


    initSearchPanel();

    initLogPanel();
    initExecuteButton();
    initStopButton();

    initLogoutPanel();
    initWelcomeIcon();
}

function initSearchPanel() {
    var scriptsListElement = document.getElementById("scripts");
    var searchPanel = document.getElementById("searchPanel");
    var searchField = document.getElementById("searchField");
    var searchButton = document.getElementById("searchButton");

    var originalSrc = searchButton.src;

    var openSearchOnTheNextClick = true;

    searchField.disabled = true;

    searchField.addEventListener("transitionend", function (e) {
        if ((e.propertyName === "width") && hasClass(searchField, "collapsed")) {
            searchField.disabled = true;
        }
    });

    searchField.addEventListener("input", function (e) {
        var searchValue = searchField.value;
        for (scriptElement of scriptsListElement) {
            if (scriptElement.innerHTML.toLowerCase().search(searchValue.toLowerCase()) !== -1) {
                show(scriptElement, "block");
            } else {
                hide(scriptElement);
            }
        }
    });

    searchButton.addEventListener("click", function () {
        if (openSearchOnTheNextClick) {
            removeClass(searchField, "collapsed");
            searchField.disabled = false;
            searchField.focus();
            searchButton.src = "../images/clear.png";

        } else {
            addClass(searchField, "collapsed");
            searchButton.src = originalSrc;
            searchField.value = "";
            for (scriptElementChild of scriptsListElement) {
                show(scriptElementChild, "block");
            }
        }
        openSearchOnTheNextClick = true;
    });

    searchButton.addEventListener("mousedown", function () {
        openSearchOnTheNextClick = hasClass(searchField, "collapsed");
    });

    searchField.addEventListener("blur", function () {
        var searchValue = searchField.value;
        if (searchValue === "") {
            addClass(searchField, "collapsed");
            searchButton.src = originalSrc;
        }
    });
}

function stopRunningScript() {
    if (runningScriptExecutor != null) {
        if (!runningScriptExecutor.isFinished()) {
            var abort = confirm("Some script is running. Do you want to abort it?");
            if (abort == true) {
                runningScriptExecutor.abort();
            } else {
                return false;
            }
        }

        runningScriptExecutor = null;
    }

    return true;
}

function initLogPanel() {
    var logPanel = document.getElementById("logPanel");

    hide(logPanel);

    var wasBottom = true;
    logPanel.addEventListener("scroll", function () {
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
    });

    var mouseDown = false;
    logPanel.addEventListener("mousedown", function () {
        mouseDown = true;
    });

    logPanel.addEventListener("mouseup", function () {
        mouseDown = false;
    });

    var updateScroll = function (mutations) {
        if ((wasBottom) && (!mouseDown)) {
            logPanel.scrollTop = logPanel.scrollHeight;
        } else {
            logPanel.onscroll();
        }
    };

    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
    var observer = new MutationObserver(updateScroll);

    window.addEventListener("resize", function (event) {
        updateScroll([]);
    });

    var config = {attributes: false, subtree: true, childList: true, characterData: true};
    observer.observe(logPanel, config);
}

function initStopButton() {
    var stopButton = document.getElementById("stopButton");

    stopButton.addEventListener("click", function () {
        if (runningScriptExecutor != null) {
            runningScriptExecutor.stop();
        }
    });
}

function initExecuteButton() {
    var executeButton = document.getElementById("executeButton");
    executeButton.addEventListener("click", function (e) {
        var logPanel = document.getElementById("logPanel");
        var inputPanel = document.getElementById("inputPanel");
        var errorsPanel = document.getElementById("validationPanel");
        var errorsList = document.getElementById("validationErrorsList");

        destroyChildren(errorsList);

        var errors = {};
        parameterControls.each(function (parameter, control) {
            if (!control.isValid()) {
                errors[parameter.name] = control.getValidationError();
            }
        });

        if (!isEmptyObject(errors)) {
            show(errorsPanel, "block");

            for (parameter in errors) {
                var errorLabel = document.createElement("li");
                errorLabel.innerText = parameter + ": " + errors[parameter];
                errorsList.appendChild(errorLabel);
            }

            hide(logPanel);
            return;
        }

        hide(errorsPanel);

        logPanel.innerText = "Calling the script...";
        show(logPanel, "block");

        var callParameters = [];
        parameterControls.each(function (parameter, control) {
            callParameters.push({
                name: parameter.name,
                value: control.getValue()
            })
        });

        var callBody = {
            script: selectedScript,
            parameters: callParameters
        };

        try {
            var process_id = authorizedCallHttp("scripts/execute", callBody, "POST");

            runningScriptExecutor = new ScriptController(process_id);

            var stopButton = document.getElementById("stopButton");
            setButtonEnabled(stopButton, true);
            setButtonEnabled(executeButton, false);

        } catch (error) {
            if (!(error instanceof HttpRequestError) || (error.code !== 401)) {
                logPanel.innerText = error.message;
            }
        }
    });
}

function initLogoutPanel() {
    var usernameField = document.getElementById("usernameField");
    var logoutPanel = document.getElementById("logoutPanel");

    try {
        usernameField.innerHTML = authorizedCallHttp("username");
    } catch (error) {
        if (error.code == 404) {
            hide(logoutPanel);
            return;
        } else {
            throw error;
        }
    }

    var logoutButton = document.getElementById("logoutButton");
    logoutButton.addEventListener("click", function (e) {
        if (!stopRunningScript()) {
            return;
        }

        try {
            authorizedCallHttp("logout", null, "POST");
        } catch (error) {
            if (error.code !== 405) {
                throw error;
            }
        }

        location.reload();
    });
}


function initWelcomeIcon() {
    var welcomeIcon = document.getElementById("welcomeIcon");

    var originalSrc = welcomeIcon.src;
    var welcomeCookiePanel = document.getElementById("welcomeCookieText");
    welcomeCookiePanel.addEventListener("mouseover", function (e) {
        welcomeIcon.src = "../images/cookie.png";
    });
    welcomeCookiePanel.addEventListener("mouseout", function (e) {
        welcomeIcon.src = originalSrc;
    });
}

function showScript(activeScript) {
    parameterControls.each(function (parameter, control) {
        control.onDestroy();
    });

    var welcomePanel = document.getElementById("welcomePanel");
    hide(welcomePanel);

    var contentPanel = document.getElementById("contentPanel");
    show(contentPanel, "flex");

    var validationPanel = document.getElementById("validationPanel");
    var validationErrorsList = document.getElementById("validationErrorsList");
    var errorPanel = document.getElementById("errorPanel");
    var scriptHeader = document.getElementById("scriptHeader");
    var scriptDescription = document.getElementById("scriptDescription");
    var stopButton = document.getElementById("stopButton");
    var executeButton = document.getElementById("executeButton");

    var paramsPanel = document.getElementById("parametersPanel");
    destroyChildren(paramsPanel);

    try {
        var info = authorizedCallHttp("scripts/info?name=" + activeScript);

        var parsedInfo = JSON.parse(info);

        scriptHeader.innerText = parsedInfo.name;

        scriptDescription.innerText = parsedInfo.description;
        if (!isNull(parsedInfo.description)) {
            show(scriptDescription, "block");
        } else {
            hide(scriptDescription);
        }

        parameterControls.clear();
        if (!isNull(parsedInfo.parameters)) {
            parsedInfo.parameters.forEach(function (parameter) {
                var control = createParameterControl(parameter);
                parameterControls.put(parameter, control);
            });
        }

        if (!parameterControls.isEmpty()) {
            show(paramsPanel, "block");

            parsedInfo.parameters.forEach(function (parameter) {
                var control = parameterControls.get(parameter);
                var element = control.getElement();
                addClass(element, "parameter");

                paramsPanel.appendChild(element);
                control.onAdd();
            });
        } else {
            hide(paramsPanel);
        }

        hide(validationPanel);
        destroyChildren(validationErrorsList);

        show(stopButton, "inline");
        show(executeButton, "inline");
        setButtonEnabled(executeButton, true);
        setButtonEnabled(stopButton, false);

        hide(errorPanel);

    } catch (error) {
        scriptHeader.innerText = activeScript;
        hide(paramsPanel);
        hide(scriptDescription);
        hide(validationPanel);
        hide(stopButton);
        hide(executeButton);

        if (!(error instanceof HttpRequestError) || (error.code !== 401)) {
            errorPanel.innerHTML = "Failed to load script info. Try to reload the page. Error message: <br> " + error.message;
            show(errorPanel, "block");
        }
    }

    var logPanel = document.getElementById("logPanel");
    hide(logPanel);
    logPanel.innerText = "";

    var inputPanel = document.getElementById("inputPanel");
    hide(inputPanel);
}

function createParameterControl(parameter) {

    if (parameter.withoutValue) {
        return new Checkbox(parameter.name, parameter.default);

    } else if (parameter.type == "list") {
        return new Combobox(
            parameter.name,
            parameter.default,
            parameter.required,
            parameter.values);

    } else {
        return new TextField(
            parameter.name,
            parameter.default,
            parameter.required,
            parameter.type,
            parameter.min,
            parameter.max);
    }
}


function selectScript(scriptName) {
    selectedScript = scriptName;

    scriptListeners.forEach(function (listener) {
        listener(selectedScript);
    })
}

function getHash() {
    if (location.hash == "undefined") {
        return null;
    }

    if (location.hash.length <= 1) {
        return null;
    }

    return decodeURIComponent(location.hash.substr(1));
}

function setButtonEnabled(button, enabled) {
    button.disabled = !enabled;
    if (!enabled) {
        addClass(button, "disabled");
    } else {
        removeClass(button, "disabled");
    }
}

function getValidByTypeError(value, type, min, max) {
    if (type == "int") {
        var isInteger = /^(((\-?[1-9])(\d*))|0)$/.test(value);
        if (!isInteger) {
            return getInvalidTypeError(type);
        }

        var intValue = parseInt(value);

        var minMaxValid = true;
        var minMaxError = "";
        if (!isNull(min)) {
            minMaxError += "min: " + min;

            if (intValue < parseInt(min)) {
                minMaxValid = false;
            }
        }

        if (!isNull(max)) {
            if (intValue > parseInt(max)) {
                minMaxValid = false;
            }

            if (!isEmptyString(minMaxError)) {
                minMaxError += ", ";
            }

            minMaxError += "max: " + max;
        }

        if (!minMaxValid) {
            return minMaxError;
        }

        return "";
    }

    return "";
}

function getInvalidTypeError(type) {
    if (type == "int") {
        return "integer expected";
    }

    return type + " expected";
}

function ScriptController(processId) {
    this.processId = processId;

    var inputPanel = document.getElementById("inputPanel");
    var executeButton = document.getElementById("executeButton");
    var stopButton = document.getElementById("stopButton");

    var https = location.protocol.toLowerCase() == "https:";
    var wsProtocol = https ? "wss" : "ws";
    var ws = new WebSocket(wsProtocol + "://" + window.location.host + "/scripts/execute/io/" + processId);

    var receivedData = false;
    var logPanel = document.getElementById("logPanel");

    ws.addEventListener("message", function (message) {
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

                inputField.addEventListener("keyup", function (event) {
                    if (event.keyCode == 13) {
                        ws.send(inputField.value);

                        inputField.value = "";
                    }
                });

                show(inputPanel, "block");
                inputField.focus();
            }
        });
    });

    ws.addEventListener("close", function (event) {
        setButtonEnabled(stopButton, false);
        setButtonEnabled(executeButton, true);
        runningScriptExecutor = null;

        hide(inputPanel);
    });

    this.stop = function () {
        authorizedCallHttp("scripts/execute/stop", {"processId": this.processId}, "POST");
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

function authorizedCallHttp(url, object, method, asyncHandler) {
    try {
        return callHttp(url, object, method, asyncHandler);
    } catch (error) {
        if ((error instanceof HttpRequestError) && (error.code == 401)) {
            var errorPanel = document.getElementById("errorPanel");
            var logPanel = document.getElementById("logPanel");
            var inputPanel = document.getElementById("inputPanel");

            hide(logPanel);
            hide(inputPanel);

            var link = document.createElement("a");
            link.innerHTML = "relogin";
            link.addEventListener("click", function () {
                location.reload();
            });
            link.href = "javascript:void(0)";

            errorPanel.innerHTML = "Credentials expired, please ";
            errorPanel.appendChild(link);
            show(errorPanel, "block");
        }

        throw error;
    }
}

