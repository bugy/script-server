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
    parameterControls = new Hashtable();

    var response = authorizedCallHttp((web_root ? web_root + "/" : "") + "scripts/list");

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
        scriptElement.onclick = function (e) {
            if (!stopRunningScript()) {
                return false;
            }

            return true;
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

    var activateScriptFromHash = function () {
        if (!isNull(runningScriptExecutor) && !runningScriptExecutor.isFinished()) {
            runningScriptExecutor.abort();
            runningScriptExecutor = null;
        }

        var hash = getHash();

        if (isNull(hash)) {
            selectScript(null);
            return;
        }

        var scriptName = scriptHashes.get(hash);
        if (isNull(scriptName)) {
            scriptName = hash;
        }

        if (scripts.indexOf(scriptName) != -1) {
            selectScript(scriptName);
        }
    };
    window.addEventListener('hashchange', activateScriptFromHash);
    activateScriptFromHash();


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
        for (var i = 0; i < scriptsListElement.childElementCount; ++i) {
            var scriptElement = scriptsListElement.children[i];
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
            searchButton.src = (web_root ? web_root : "") + "/images/clear.png";

        } else {
            addClass(searchField, "collapsed");
            searchButton.src = originalSrc;
            searchField.value = "";
            for (var i = 0; i < scriptsListElement.childElementCount; ++i) {
                show(scriptsListElement.children[i], "block");
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
    var logContent = document.getElementById("logContent");
    var logPanelShadow = document.getElementById("logPanelShadow");

    hide(logPanel);

    var wasBottom = true;
    var scrollStyleUpdate = function () {
        var isTop = logContent.scrollTop == 0;
        var isBottom = (logContent.scrollTop + logContent.clientHeight + 5) > (logContent.scrollHeight);

        var shadowTop = !isTop;
        var shadowBottom = !isBottom;

        if (shadowTop && shadowBottom) {
            addClass(logPanelShadow, "shadow-top-bottom");
            removeClass(logPanelShadow, "shadow-top");
            removeClass(logPanelShadow, "shadow-bottom");
        } else if (shadowTop) {
            removeClass(logPanelShadow, "shadow-top-bottom");
            addClass(logPanelShadow, "shadow-top");
            removeClass(logPanelShadow, "shadow-bottom");
        } else if (shadowBottom) {
            removeClass(logPanelShadow, "shadow-top-bottom");
            removeClass(logPanelShadow, "shadow-top");
            addClass(logPanelShadow, "shadow-bottom");
        } else {
            removeClass(logPanelShadow, "shadow-top-bottom");
            removeClass(logPanelShadow, "shadow-top");
            removeClass(logPanelShadow, "shadow-bottom");
        }

        wasBottom = isBottom;
    };
    logContent.addEventListener("scroll", scrollStyleUpdate);

    var mouseDown = false;
    logContent.addEventListener("mousedown", function () {
        mouseDown = true;
    });

    logContent.addEventListener("mouseup", function () {
        mouseDown = false;
    });

    var updateScroll = function (mutations) {
        if ((wasBottom) && (!mouseDown)) {
            logContent.scrollTop = logContent.scrollHeight;
        } else {
            scrollStyleUpdate();
        }
    };

    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
    var observer = new MutationObserver(updateScroll);

    window.addEventListener("resize", function (event) {
        updateScroll([]);
    });

    var config = {attributes: false, subtree: true, childList: true, characterData: true};
    observer.observe(logContent, config);
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
        var logContent = document.getElementById("logContent");
        var inputPanel = document.getElementById("inputPanel");
        var errorsPanel = document.getElementById("validationPanel");
        var errorsList = document.getElementById("validationErrorsList");
        var filesDownloadPanel = document.getElementById("filesDownloadPanel");

        destroyChildren(errorsList);
        destroyChildren(filesDownloadPanel);
        hide(filesDownloadPanel);

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

        logContent.innerText = "Calling the script...";
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
            var process_id = authorizedCallHttp((web_root ? web_root + "/" : "") + "scripts/execute", callBody, "POST");

            runningScriptExecutor = new ScriptController(process_id);

            var stopButton = document.getElementById("stopButton");
            setButtonEnabled(stopButton, true);
            setButtonEnabled(executeButton, false);

        } catch (error) {
            if (!(error instanceof HttpRequestError) || (error.code !== 401)) {
                logContent.innerText = error.message;
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
        welcomeIcon.src = (web_root ? web_root : "") + "/images/cookie.png";
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

    var contentPanel = document.getElementById("contentPanel");

    var validationPanel = document.getElementById("validationPanel");
    var validationErrorsList = document.getElementById("validationErrorsList");
    var errorPanel = document.getElementById("errorPanel");
    var scriptHeader = document.getElementById("scriptHeader");
    var scriptDescription = document.getElementById("scriptDescription");
    var stopButton = document.getElementById("stopButton");
    var executeButton = document.getElementById("executeButton");

    var paramsPanel = document.getElementById("parametersPanel");
    destroyChildren(paramsPanel);

    if (isNull(activeScript)) {
        show(welcomePanel, 'flex');
        hide(contentPanel);
        return;
    }

    hide(welcomePanel);
    show(contentPanel, "flex");

    try {
        var info = authorizedCallHttp((web_root ? web_root + "/" : "") + "scripts/info?name=" + activeScript);
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
    var logContent = document.getElementById("logContent");
    hide(logPanel);
    logContent.innerText = "";

    var inputPanel = document.getElementById("inputPanel");
    hide(inputPanel);

    var filesDownloadPanel = document.getElementById("filesDownloadPanel");
    destroyChildren(filesDownloadPanel);
    hide(filesDownloadPanel);
}

function createParameterControl(parameter) {
    if (parameter.withoutValue) {
        return new Checkbox(parameter.name, parameter.default, parameter.description);

    } else if (parameter.type == "list") {
        return new Combobox(
            parameter.name,
            parameter.default,
            parameter.required,
            parameter.values,
            parameter.description);

    } else {
        return new TextField(
            parameter.name,
            parameter.default,
            parameter.required,
            parameter.type,
            parameter.min,
            parameter.max,
            parameter.description,
            parameter.secure);
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
    var ws = new WebSocket(wsProtocol + "://" + window.location.host + (web_root ? web_root : "") + "/scripts/execute/io/" + processId);

    var receivedData = false;
    var logContent = document.getElementById("logContent");

    var logElements = [];
    var publishLogs = function () {
        for (i = 0; i < logElements.length; i++) {
            logContent.appendChild(logElements[i]);
        }
        logElements = [];
    };
    var logPublisher = window.setInterval(publishLogs, 30);

    ws.addEventListener("message", function (message) {
        if (!receivedData) {
            logContent.innerText = "";
            receivedData = true;
        }

        var event = JSON.parse(message.data);

        var eventType = event.event;
        var data = event.data;

        if (eventType == "output") {
            var outputElement = null;

            if (!isNull(data.text_color) || !isNull(data.background_color) || !isNull(data.text_styles)) {
                outputElement = document.createElement('span');
                if (!isNull(data.text_color)) {
                    addClass(outputElement, 'text_color_' + data.text_color);
                }
                if (!isNull(data.background_color)) {
                    addClass(outputElement, 'background_' + data.background_color);
                }

                if (!isNull(data.text_styles)) {
                    for (styleIndex = 0; styleIndex < data.text_styles.length; styleIndex++) {
                        addClass(outputElement, 'text_style_' + data.text_styles[styleIndex]);
                    }
                }

                outputElement.appendChild(document.createTextNode(data.text));
            } else {
                outputElement = document.createTextNode(data.text);
            }

            logElements.push(outputElement);

            return;

        } else if (eventType == "input") {
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

        } else if (eventType == "file") {
            var filesDownloadPanel = document.getElementById('filesDownloadPanel');
            show(filesDownloadPanel, 'block');

            var url = data.url;
            var filename = data.filename;

            var downloadLink = document.createElement('a');
            addClass(downloadLink, 'waves-effect');
            addClass(downloadLink, 'waves-teal');
            addClass(downloadLink, 'btn-flat');
            downloadLink.setAttribute("download", filename);
            downloadLink.href = url;
            downloadLink.target = '_blank';
            downloadLink.appendChild(document.createTextNode(filename));

            var downloadImage = document.createElement('img');
            downloadImage.src = (web_root ? web_root : "") + 'images/file_download.png';
            downloadLink.appendChild(downloadImage);

            filesDownloadPanel.appendChild(downloadLink);

            return;
        }
    });

    ws.addEventListener("close", function (event) {
        window.clearInterval(logPublisher);
        publishLogs();

        setButtonEnabled(stopButton, false);
        setButtonEnabled(executeButton, true);
        runningScriptExecutor = null;

        hide(inputPanel);
    });

    this.stop = function () {
        authorizedCallHttp((web_root ? web_root + "/" : "") + "scripts/execute/stop", {"processId": this.processId}, "POST");
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

