import Vue from 'vue';
import Vuex from 'vuex';
import {
    callHttp,
    contains,
    forEachKeyValue,
    HttpRequestError,
    HttpUnauthorizedError,
    isEmptyArray,
    isEmptyString,
    isNull,
    isWebsocketClosed,
    logError,
    removeElement,
    SocketClosedError,
    toDict
} from '../common';
import {ReactiveWebSocket} from '../connections/rxWebsocket';
import {comboboxTypes, preprocessParameter} from './model_helper'
import {ScriptExecutor} from './script-execution-model';
import ScriptView from './script-view';
import {
    ADD_DOWNLOADABLE_FILE,
    ADD_PARAMETER,
    APPEND_LOG_CHUNK,
    REMOVE_PARAMETER,
    RESET_DOWNLOADABLE_FILES,
    SEND_USER_INPUT,
    SEND_VALUE_TO_SERVER,
    SET_ALL_PARAMETER_VALUES,
    SET_EXECUTING,
    SET_INPUT_PROMPT,
    SET_LOG,
    SET_PARAMETER_VALUE,
    SET_PARAMETERS,
    SET_SCRIPT_CONFIG,
    START_EXECUTION,
    STOP_EXECUTION,
    UPDATE_PARAMETER,
    UPDATE_PARAMETERS
} from './vuex_constants';

Vue.use(Vuex);

export function ScriptController(scriptName, parent, executionStartCallback, loadFinishedCallback, loadErrorCallback) {
    this.scriptName = scriptName;
    this.executionStartCallback = executionStartCallback;
    this.scriptView = null;
    this.parentPanel = parent;

    this.logPublisher = null;
    this.logLastIndex = 0;
    this.executor = null;
    this.executorListener = null;

    this._reconnectionAttempt = 0;

    this._store = this._initStore();

    this._reconnect(loadFinishedCallback, loadErrorCallback);
}

ScriptController.prototype._reconnect = function (loadFinishedCallback, loadErrorCallback) {
    var controller = this;

    if (!isNull(this.websocket) && !isWebsocketClosed(this.websocket)) {
        this.websocket.close();
        this.websocket = null;
    }

    var dataReceived = false;

    var socket = new ReactiveWebSocket('scripts/' + this.scriptName, {
        onNext: function (rawMessage) {
            dataReceived = true;
            controller._reconnectionAttempt = 0;

            var event = JSON.parse(rawMessage.data);

            var eventType = event.event;
            var data = event.data;

            if (isNull(controller.scriptConfig) && (eventType !== 'initialConfig')) {
                loadErrorCallback('Unexpected error occurred', new Error('invalid message from the server'));
                socket.close();
                return;
            }

            if (eventType === 'initialConfig') {
                const firstLoad = isNull(controller.scriptConfig);

                controller._updateScriptConfig(data);
                if (firstLoad && loadFinishedCallback) {
                    loadFinishedCallback(data);
                }

                return;
            }

            if (eventType === 'parameterChanged') {
                controller._store.commit(UPDATE_PARAMETER, data);
                return;
            }

            if (eventType === 'parameterAdded') {
                controller._store.commit(ADD_PARAMETER, data);
                return;
            }

            if (eventType === 'parameterRemoved') {
                controller._store.commit(REMOVE_PARAMETER, data);
                return;
            }
        },

        onError: function (error) {
            if (error instanceof SocketClosedError) {
                console.log('Socket closed. code=' + error.code + ', reason=' + error.reason);
                logError(error);

                if (isNull(controller.scriptConfig)) {
                    loadErrorCallback('Failed to connect to the server', new Error('Failed to connect to the server'));
                    return;
                }

                controller._reconnectionAttempt++;

                if (controller._reconnectionAttempt > 5) {
                    loadErrorCallback('Failed to reconnect', new Error('Failed to reconnect'));
                    return;
                }

                setTimeout(function () {
                    console.log('Trying to reconnect. Attempt ' + controller._reconnectionAttempt);
                    controller._reconnect(loadFinishedCallback, loadErrorCallback);
                }, (controller._reconnectionAttempt - 1) * 500);

                return;
            }

            if (error instanceof HttpUnauthorizedError) {
                loadErrorCallback(error.message, error);
                return;
            }

            loadErrorCallback('Unexpected error occurred', error);
        },

        onComplete: function () {
            console.log('Websocket completed. This should not be possible for a config socket');
            loadErrorCallback('Connection to server closed', new Error('Connection to server closed: ' + event.reason));
        }
    });

    this.websocket = socket;
};

ScriptController.prototype._fillView = function (parent) {
    const store = this._store;

    this.scriptView = new Vue({
        store,
        render(createElement) {
            return createElement(ScriptView)
        }
    });

    var container = document.createElement('div');
    container.id = this.scriptView.id;
    container.className = 'script-panel';
    parent.appendChild(container);

    this.scriptView.$mount(container)
};

ScriptController.prototype._updateScriptConfig = function (scriptConfig) {
    var oldConfig = this.scriptConfig;
    this.scriptConfig = scriptConfig;
    this._store.commit(SET_SCRIPT_CONFIG, scriptConfig);

    if (isNull(oldConfig)) {
        this._fillView(this.parentPanel);
        this._store.commit(SET_PARAMETERS, this.scriptConfig.parameters);
    } else {
        this._store.commit(UPDATE_PARAMETERS, this.scriptConfig.parameters);
    }
};

ScriptController.prototype.destroy = function () {
    if (!isNull(this.websocket)) {
        this.websocket.close();
    }

    this._stopLogPublisher();

    this.scriptView.$destroy();

    if (!isNull(this.executor)) {
        this.executor.removeListener(this.executorListener);
    }
};

ScriptController.prototype.setExecutor = function (executor) {
    this.executor = executor;

    if (this.scriptConfig != null) {
        this._setParameterValues(executor.parameterValues);

        this._store.commit(SET_EXECUTING, true);
        this._updateViewWithExecutor(executor);
    }
};

ScriptController.prototype._updateViewWithExecutor = function (executor) {
    this._startLogPublisher();

    this.executorListener = {
        'onExecutionStop': function () {
            this._publishLogs();
            this._stopLogPublisher();

            this._store.commit(SET_EXECUTING, false);
            this._store.commit(SET_INPUT_PROMPT, null);
        }.bind(this),

        'onInputPrompt': promptText => {
            this._store.commit(SET_INPUT_PROMPT, promptText);
        },

        'onFileCreated': function (url, filename) {
            this._store.commit(ADD_DOWNLOADABLE_FILE, [url, filename]);
        }.bind(this)
    };

    executor.addListener(this.executorListener);
};

ScriptController.prototype._startLogPublisher = function () {
    this._stopLogPublisher();

    this.logLastIndex = 0;

    this._publishLogs();
    this.logPublisher = window.setInterval(this._publishLogs.bind(this), 30);
};

ScriptController.prototype._stopLogPublisher = function () {
    if (!isNull(this.logPublisher)) {
        window.clearInterval(this.logPublisher);
        this.logPublisher = null;
    }
};

ScriptController.prototype._publishLogs = function () {
    if (isNull(this.scriptView)) {
        return;
    }

    var logChunks = this.executor.logChunks;

    if ((this.logLastIndex === 0) && (logChunks.length > 0)) {
        this._store.commit(SET_LOG, '');
    }

    for (; this.logLastIndex < logChunks.length; this.logLastIndex++) {
        var logIndex = this.logLastIndex;

        var logChunk = logChunks[logIndex];

        this._store.commit(APPEND_LOG_CHUNK, logChunk);
    }
};

ScriptController.prototype._initStore = function () {
    var controller = this;

    function ensureListValueExists(value, parameter) {
        if (Array.isArray(value)) {
            if (isEmptyArray(parameter.values)) {
                parameter.values = value.splice();
            } else {
                for (let j = 0; j < value.length; j++) {
                    const valueElement = value[j];
                    if (!contains(parameter.values, valueElement)) {
                        parameter.values.push(valueElement);
                    }
                }
            }
        } else {
            if (isEmptyArray(parameter.values)) {
                parameter.values = [value];
            } else if (!contains(parameter.values, value)) {
                parameter.values.push(value);
            }
        }
    }

    function _preprocessParameter(parameter, store) {
        preprocessParameter(parameter, (path) => {
            return store.dispatch('loadFiles', {parameterName: parameter.name, path})
        });
    }

    return new Vuex.Store({
        strict: true,

        state: {
            scriptConfig: null,
            parameters: [],
            parameterValues: {},
            parameterErrors: {},
            executing: false,
            showLog: false,
            downloadableFiles: [],
            inputPromptText: null,
            sentValues: {},
            logChunks: []
        },

        mutations: {
            [SET_SCRIPT_CONFIG](state, scriptConfig) {
                state.scriptConfig = scriptConfig;
            },

            [SET_PARAMETERS](state, parameters) {
                var parameterValues = {};

                for (var i = 0; i < parameters.length; i++) {
                    var parameter = parameters[i];

                    _preprocessParameter(parameter, this);

                    if (!isNull(parameter.default)) {
                        parameterValues[parameter.name] = parameter.default;
                    } else {
                        parameterValues[parameter.name] = null;
                    }
                }

                state.parameters = parameters;
                state.parameterValues = parameterValues;
            },

            [UPDATE_PARAMETERS](state, newParameters) {
                const oldParametersDict = toDict(state.parameters, 'name');
                const newParametersDict = toDict(newParameters, 'name');

                forEachKeyValue(oldParametersDict, function (name, parameter) {
                    if (name in newParametersDict) {
                        return;
                    }

                    removeElement(state.parameters, parameter);
                });

                forEachKeyValue(newParametersDict, (name, parameter) => {
                    _preprocessParameter(parameter, this);

                    if (name in oldParametersDict) {
                        const index = state.parameters.indexOf(oldParametersDict[name]);
                        Vue.set(state.parameters, index, parameter);
                    } else {
                        state.parameters.push(parameter);
                    }
                });

                controller.scriptView.$nextTick(function () {
                    const parameterValues = state.parameterValues;
                    const parameterErrors = state.parameterErrors;

                    forEachKeyValue(parameterValues, function (key, value) {
                        const errorMessage = parameterErrors[key];
                        const valueToSend = isEmptyString(errorMessage) ? value : null;

                        controller._sendCurrentValue(key, valueToSend);
                    });
                });
            },

            [ADD_PARAMETER](state, parameter) {
                _preprocessParameter(parameter, this);
                state.parameters.push(parameter);
            },

            [UPDATE_PARAMETER](state, parameter) {
                let foundIndex = -1;

                const parameters = state.parameters;

                for (let i = 0; i < parameters.length; i++) {
                    const anotherParam = parameters[i];
                    if (anotherParam['name'] === parameter['name']) {
                        foundIndex = i;
                        break;
                    }
                }

                if (foundIndex < 0) {
                    console.log('Failed to find parameter ' + parameter['name']);
                    return;
                }

                _preprocessParameter(parameter, this);
                Vue.set(parameters, foundIndex, parameter);
            },

            [REMOVE_PARAMETER](state, parameterName) {
                let foundIndex = -1;

                const parameters = state.parameters;

                for (let i = 0; i < parameters.length; i++) {
                    const parameter = parameters[i];

                    if (parameter['name'] === parameterName) {
                        foundIndex = i;
                        break;
                    }
                }

                if (foundIndex < 0) {
                    console.log('Failed to find parameter ' + parameterName);
                    return;
                }

                parameters.splice(foundIndex, 1);
            },

            [SET_PARAMETER_VALUE](state, {parameterName, value, errorMessage}) {
                state.parameterErrors[parameterName] = errorMessage;
                state.parameterValues[parameterName] = value;

                const valueToSend = isEmptyString(errorMessage) ? value : null;

                if (state.sentValues[parameterName] !== valueToSend) {
                    this.dispatch(SEND_VALUE_TO_SERVER, {parameterName, valueToSend});
                }
            },

            [SET_ALL_PARAMETER_VALUES](state, values) {
                for (var i = 0; i < state.parameters.length; i++) {
                    var parameter = state.parameters[i];
                    var parameterName = parameter.name;

                    var value = values[parameterName];

                    let valueToSet;
                    if (!isNull(value)) {
                        if ((comboboxTypes.includes(parameter.type))) {
                            ensureListValueExists(value, parameter);
                        }

                        valueToSet = value;
                    } else {
                        valueToSet = null;
                    }

                    state.parameterValues[parameterName] = valueToSet;
                    this.dispatch(SEND_VALUE_TO_SERVER, {parameterName, valueToSend: valueToSet});
                }
            },

            [SET_EXECUTING](state, executing) {
                state.executing = executing;

                if (executing) {
                    state.showLog = true;
                }
            },

            [SET_INPUT_PROMPT](state, promptText) {
                state.inputPromptText = promptText;
            },

            [RESET_DOWNLOADABLE_FILES](state) {
                state.downloadableFiles = []
            },

            [ADD_DOWNLOADABLE_FILE](state, [url, filename]) {
                state.downloadableFiles.push({url, filename});
            },

            _setSentValue(state, [parameterName, value]) {
                state.sentValues[parameterName] = value;
            },

            [SET_LOG](state, log) {
                state.logChunks = [{text: log}]
            },

            [APPEND_LOG_CHUNK](state, logChunk) {
                state.logChunks.push(logChunk);
            }
        },

        actions: {
            [SEND_USER_INPUT]({state}, inputText) {
                if (!isEmptyString(state.inputPromptText)) {
                    controller.executor.sendUserInput(inputText);
                }
            },

            [SEND_VALUE_TO_SERVER]({commit}, {parameterName, valueToSend}) {
                controller._sendCurrentValue(parameterName, valueToSend);
                commit('_setSentValue', [parameterName, valueToSend]);
            },

            [START_EXECUTION]({state, commit}) {
                var parameterValues = $.extend({}, state.parameterValues);

                commit(SET_EXECUTING, true);
                commit(SET_LOG, 'Calling the script...');

                try {
                    controller.executor = new ScriptExecutor(state.scriptConfig.name);
                    controller.executor.start(parameterValues);
                    controller.executionStartCallback(controller.executor);

                    controller._updateViewWithExecutor(controller.executor);

                } catch (error) {
                    commit(SET_EXECUTING, false);

                    if (!(error instanceof HttpUnauthorizedError)) {
                        logError(error);

                        commit(APPEND_LOG_CHUNK, {text: '\n\n' + error.message});
                    }
                }

            },

            [STOP_EXECUTION]() {
                if (!isNull(controller.executor)) {
                    controller.executor.stop();
                }
            },

            loadFiles({state, commit}, {parameterName, path}) {
                const scriptConfig = state.scriptConfig;
                if (isNull(scriptConfig)) {
                    throw Error('Config is not available');
                }

                const url = encodeURI('scripts/' + scriptConfig.name + '/' + parameterName + '/list-files');
                const param = $.param({'path': path, 'id': scriptConfig.id}, true);
                const full_url = url + '?' + param;

                return new Promise(((resolve, reject) => {
                    callHttp(full_url, null, 'GET',
                        response => resolve(JSON.parse(response)),
                        (code, message) => reject(new HttpRequestError(code, message))
                    );
                }));
            }
        }
    });
};

ScriptController.prototype._sendCurrentValue = function (parameter, value) {
    if ((isNull(this.websocket))) {
        return;
    }

    var data = {};
    data['parameter'] = parameter;
    data['value'] = value;
    this.websocket.send(JSON.stringify({
        'event': 'parameterValue',
        'data': data
    }));
};

ScriptController.prototype.setParameterValues = function (values) {
    this._setParameterValues(values);
};

ScriptController.prototype._setParameterValues = function (values) {
    this._store.commit(SET_ALL_PARAMETER_VALUES, values);
};
