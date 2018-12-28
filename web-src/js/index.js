import {
    addClass,
    callHttp,
    clearArray,
    createTemplateElement,
    destroyChildren,
    getUnparameterizedUrl,
    hasClass,
    hide,
    HttpRequestError,
    HttpUnauthorizedError,
    isEmptyObject,
    isNull,
    logError,
    readQueryParameters,
    removeClass,
    removeElements,
    show
} from './common';

import './connections/rxWebsocket.js';
import {ScriptController} from './script/script-controller';
import {restoreExecutor} from './script/script-execution-model';
import './style_imports.js';

let selectedScript = null;
const scriptSelectionListeners = [];
const scriptMenuItems = new Map();
const runningScriptExecutors = [];
let activeScriptController = null;

window.onload = onLoad;

function onLoad() {
    authorizedCallHttp('conf/title', null, 'GET', function (result) {
        if (result) {
            document.title = result;
        }
    });

    var response = authorizedCallHttp("scripts/list");

    var scripts = JSON.parse(response);

    var scriptsListElement = document.getElementById("scripts");

    scripts.sort(function (name1, name2) {
        return name1.toLowerCase().localeCompare(name2.toLowerCase());
    });

    var scriptHashes = new Map();

    scripts.forEach(function (script) {
        var scriptElement = document.createElement("a");

        var scriptHash = script.replace(/\s/g, "_");
        scriptHashes.set(scriptHash, script);

        addClass(scriptElement, "collection-item");
        addClass(scriptElement, "waves-effect");
        addClass(scriptElement, "waves-teal");
        scriptElement.setAttribute("href", "#" + scriptHash);
        scriptElement.innerText = script;

        scriptSelectionListeners.push(function (activeScript) {
            if (activeScript === script) {
                addClass(scriptElement, "active");
            } else {
                removeClass(scriptElement, "active");
            }
        });

        var stateElement = createTemplateElement('menu-item-state-template');
        scriptElement.appendChild(stateElement);

        scriptsListElement.appendChild(scriptElement);

        scriptElement.stateElement = stateElement;
        scriptMenuItems.set(script, scriptElement);

        updateMenuItemState(script);
    });

    var contentPanel = document.getElementById('content-panel');
    hide(contentPanel);

    scriptSelectionListeners.push(function (activeScript, parameterValues) {
        showScript(activeScript, parameterValues);
    });

    var activateScriptFromHash = function () {
        var hash = getHash();

        if (isNull(hash)) {
            selectScript(null);
            return;
        }

        var scriptName = scriptHashes.get(hash);
        if (isNull(scriptName)) {
            scriptName = hash;
        }

        if (scripts.indexOf(scriptName) !== -1) {
            var queryParameters = readQueryParameters();
            if (isEmptyObject(queryParameters)) {
                queryParameters = null;
            }

            selectScript(scriptName, queryParameters);

            if (!isEmptyObject(queryParameters)) {
                history.pushState('', '', getUnparameterizedUrl() + window.location.hash)
            }
        }
    };
    window.addEventListener('hashchange', activateScriptFromHash);
    activateScriptFromHash();

    window.addEventListener("beforeunload", function (e) {
        if (getUnfinishedExecutors().length > 0) {
            e = e || window.event;

            // in modern browsers the message will be replaced with default one (security reasons)
            var message = "Closing the page will stop all running scripts. Are you sure?";
            e.returnValue = message;

            return message;
        }
    });


    initSearchPanel();

    initWelcomeIcon();

    loadActiveExecutions();

    initAuthBasedElements();
}

function loadActiveExecutions() {
    authorizedCallHttp('scripts/execution/active', null, null, function (response) {
        var activeExecutionIds = JSON.parse(response);
        for (var i = 0; i < activeExecutionIds.length; i++) {
            var executionId = activeExecutionIds[i];
            restoreExecutor(executionId, function (executor) {
                addRunningExecutor(executor);

                if (selectedScript === executor.scriptName) {
                    selectScript(executor.scriptName);
                }
            });
        }
    });
}

function initSearchPanel() {
    var scriptsListElement = document.getElementById("scripts");
    var searchPanel = document.getElementById("searchPanel");
    var searchField = document.getElementById("searchField");
    var searchButton = document.getElementById("searchButton");

    var originalSrc = searchButton.src;

    var openSearchOnTheNextClick = true;

    searchField.disabled = true;

    searchPanel.addEventListener("transitionend", function (e) {
        if ((e.propertyName === "width") && hasClass(searchPanel, "collapsed")) {
            searchField.disabled = true;
        }
    });

    searchField.addEventListener('input', function () {
        var searchValue = searchField.value;
        for (var i = 0; i < scriptsListElement.childElementCount; ++i) {
            var scriptElement = scriptsListElement.children[i];
            if (scriptElement.innerHTML.toLowerCase().search(searchValue.toLowerCase()) !== -1) {
                show(scriptElement);
            } else {
                hide(scriptElement);
            }
        }
    });

    searchButton.addEventListener("click", function () {
        if (openSearchOnTheNextClick) {
            removeClass(searchPanel, "collapsed");
            searchField.disabled = false;
            searchField.focus();
            searchButton.src = "images/clear.png";

        } else {
            addClass(searchPanel, "collapsed");
            searchButton.src = originalSrc;
            searchField.value = "";
            for (var i = 0; i < scriptsListElement.childElementCount; ++i) {
                show(scriptsListElement.children[i]);
            }
        }
        openSearchOnTheNextClick = true;
    });

    searchButton.addEventListener("mousedown", function () {
        openSearchOnTheNextClick = hasClass(searchPanel, "collapsed");
    });

    searchField.addEventListener("blur", function () {
        var searchValue = searchField.value;
        if (searchValue === "") {
            addClass(searchPanel, "collapsed");
            searchButton.src = originalSrc;
        }
    });
}

function getUnfinishedExecutors() {
    var unfinishedExecutors = [];
    runningScriptExecutors.forEach(function (executor) {
        if (!executor.isFinished()) {
            unfinishedExecutors.push(executor);
        }
    });
    return unfinishedExecutors;
}

function stopRunningScripts() {
    if (runningScriptExecutors.length > 0) {
        var unfinishedExecutors = getUnfinishedExecutors();

        if (unfinishedExecutors.length > 0) {
            var message;
            if (unfinishedExecutors.length === 1) {
                message = 'Some script is running. Do you want to abort it?'
            } else {
                message = unfinishedExecutors.length + ' scripts are running. Do you want to abort them?'
            }

            var abort = confirm(message);
            if (abort === true) {
                unfinishedExecutors.forEach(function (executor) {
                    executor.abort();
                });
            } else {
                return false;
            }
        }

        clearArray(runningScriptExecutors);
    }

    return true;
}

function initAuthBasedElements() {
    const logoutPanel = document.getElementById("logoutPanel");
    hide(logoutPanel);

    authorizedCallHttp('auth/info', null, 'GET', function (response) {
        var authInfo = JSON.parse(response);

        if (authInfo.enabled) {
            initLogoutPanel(authInfo.username);
        }

        if (authInfo.admin) {
            show(document.getElementById('adminLink'));
            hide(document.getElementById('githubLink'));
        }
    });
}

function initLogoutPanel(username) {
    var usernameField = document.getElementById("usernameField");
    var logoutPanel = document.getElementById("logoutPanel");

    show(logoutPanel);

    usernameField.innerText = username;

    var logoutButton = document.getElementById("logoutButton");
    logoutButton.addEventListener("click", function () {
        if (!stopRunningScripts()) {
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
    var welcomeIcon = document.getElementById('welcome-icon');

    var originalSrc = welcomeIcon.src;
    var welcomeCookiePanel = document.getElementById('welcome-cookie-text');
    welcomeCookiePanel.addEventListener('mouseover', function () {
        welcomeIcon.src = 'images/cookie.png';
    });
    welcomeCookiePanel.addEventListener('mouseout', function () {
        welcomeIcon.src = originalSrc;
    });
}

function addRunningExecutor(scriptExecutor) {
    runningScriptExecutors.push(scriptExecutor);
    updateMenuItemState(scriptExecutor.scriptName);

    scriptExecutor.addListener({
        'onExecutionStop': function () {
            updateMenuItemState(scriptExecutor.scriptName);
        }
    })
}

function showScript(selectedScript, parameterValues) {
    if (!isNull(activeScriptController)) {
        var previousScriptName = activeScriptController.scriptName;
        var executorsToRemove = runningScriptExecutors.filter(function (executor) {
            return (executor.scriptName === previousScriptName) && executor.isFinished();
        });

        if (executorsToRemove.length > 0) {
            removeElements(runningScriptExecutors, executorsToRemove);

            updateMenuItemState(previousScriptName);
        }

        activeScriptController.destroy();
        activeScriptController = null;
    }

    var welcomePanel = document.getElementById('welcome-panel');
    var contentPanel = document.getElementById('content-panel');

    if (isNull(selectedScript)) {
        show(welcomePanel, 'flex');
        hide(contentPanel);
        return;
    }

    hide(welcomePanel);
    show(contentPanel);

    var scriptPanelContainer = document.getElementById('script-panel-container');
    destroyChildren(scriptPanelContainer);

    hideErrorPanel();

    var scriptHeader = document.getElementById('script-header');

    var scriptExecutor = findRunningExecutor(selectedScript);

    scriptHeader.innerText = selectedScript;

    const scriptController = new ScriptController(
        selectedScript,
        scriptPanelContainer,
        function (scriptExecutor) {
            addRunningExecutor(scriptExecutor);
        },
        function () {
            if (!isNull(scriptExecutor)) {
                scriptController.setExecutor(scriptExecutor);
            } else if (!isNull(parameterValues)) {
                scriptController.setParameterValues(parameterValues);
            }
        },
        function (message, error) {
            logError(error);

            //noinspection JSDuplicatedDeclaration
            var errorPanel = showErrorPanel('Failed to load script info. Try to reload the page.'
                + ' Error message:');
            errorPanel.appendChild(document.createElement('br'));
            errorPanel.appendChild(document.createTextNode(message));
        });

    activeScriptController = scriptController;
}

function findRunningExecutor(selectedScript) {
    var scriptExecutor = null;
    runningScriptExecutors.forEach(function (executor) {
        if (executor.scriptName === selectedScript) {
            scriptExecutor = executor;
        }
    });
    return scriptExecutor;
}

function selectScript(scriptName, parameterValues) {
    selectedScript = scriptName;

    scriptSelectionListeners.forEach(function (listener) {
        listener(selectedScript, parameterValues);
    })
}

function getHash() {
    if (location.hash === 'undefined') {
        return null;
    }

    if (location.hash.length <= 1) {
        return null;
    }

    return decodeURIComponent(location.hash.substr(1));
}

function updateMenuItemState(scriptName) {
    var executing = false;
    var finished = false;

    runningScriptExecutors.forEach(function (executor) {
        if (executor.scriptName !== scriptName) {
            return;
        }

        if (executor.isFinished()) {
            finished = true;
        } else {
            executing = true;
        }
    });

    var state = null;
    if (executing) {
        state = 'executing';
    } else if (finished) {
        state = 'finished';
    }

    var menuItem = scriptMenuItems.get(scriptName);
    var stateElement = menuItem.stateElement;

    removeClass(stateElement, 'finished');
    removeClass(stateElement, 'executing');

    if (!isNull(state)) {
        addClass(stateElement, state);
    }
}

export function authorizedCallHttp(url, object, method, asyncHandler) {
    try {
        return callHttp(url, object, method, asyncHandler);
    } catch (error) {
        if ((error instanceof HttpRequestError) && (error.code === 401)) {
            var link = document.createElement('a');
            link.innerHTML = 'relogin';
            link.addEventListener('click', function () {
                location.reload();
            });
            link.href = 'javascript:void(0)';

            var errorPanel = showErrorPanel('Credentials expired, please ');
            errorPanel.appendChild(link);

            throw new HttpUnauthorizedError(error.code, 'User is not authenticated');
        }

        throw error;
    }
}

function showErrorPanel(text) {
    var errorPanel = document.getElementById('error-panel');

    var scriptPanelContainer = document.getElementById('script-panel-container');
    addClass(scriptPanelContainer, 'collapsed');

    var hideThis = function () {
        hide(this);
    };
    $(scriptPanelContainer).find('.log-panel').each(hideThis);
    $(scriptPanelContainer).find('.script-input-panel').each(hideThis);
    $(scriptPanelContainer).find('.validation-panel').each(hideThis);

    destroyChildren(errorPanel);
    errorPanel.innerText = text;

    show(errorPanel);

    return errorPanel;
}

function hideErrorPanel() {
    var errorPanel = document.getElementById('error-panel');
    errorPanel.innerHTML = '';

    var scriptPanelContainer = document.getElementById('script-panel-container');
    removeClass(scriptPanelContainer, 'collapsed');

    hide(errorPanel);
}