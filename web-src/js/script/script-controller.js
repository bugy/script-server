'use strict';

function ScriptController(scriptName, parent, executionStartCallback, loadErrorCallback) {
    this.scriptName = scriptName;
    this.executionStartCallback = executionStartCallback;
    this.scriptView = null;
    this.parentPanel = parent;

    this.logPublisher = null;
    this.logLastIndex = 0;
    this.executor = null;
    this.executorListener = null;

    this._reconnectionAttempt = 0;

    this._initParametersModel();

    this._reconnect(loadErrorCallback);
}

ScriptController.prototype._reconnect = function (loadErrorCallback) {
    var controller = this;

    if (!isNull(this.websocket) && !isWebsocketClosed(this.websocket)) {
        this.websocket.close();
        this.websocket = null;
    }

    var dataReceived = false;

    var socket = new ReactiveWebSocket('scripts/info/' + this.scriptName, {
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
                controller._updateScriptConfig(data);
                return;
            }

            if (eventType === 'parameterChanged') {
                controller._updateParameter(data);
                return;
            }

            if (eventType === 'parameterAdded') {
                controller._addParameter(data);
                return;
            }

            if (eventType === 'parameterRemoved') {
                controller._removeParameter(data);
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
                    controller._reconnect(loadErrorCallback);
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

ScriptController.prototype._fillView = function (parent, scriptConfig) {
    var scriptView = new ScriptView(parent, this.parametersModel);
    this.scriptView = scriptView;

    scriptView.setScriptDescription(scriptConfig.description);

    scriptView.setExecutionCallback(function () {
        var parameterValues = $.extend({}, this.parametersModel.state.parameterValues);

        this.scriptView.setExecuting();
        scriptView.setLog('Calling the script...');

        try {
            this.executor = new ScriptExecutor(scriptConfig.name);
            this.executor.start(parameterValues);
            this.executionStartCallback(this.executor);

            this._updateViewWithExecutor(this.executor);

        } catch (error) {
            this.scriptView.setStopEnabled(false);
            this.scriptView.setExecutionEnabled(true);

            if (!(error instanceof HttpUnauthorizedError)) {
                logError(error);

                var errorLogElement = '\n\n' + error.message;
                scriptView.appendLog(errorLogElement);
            }
        }
    }.bind(this));

    scriptView.setStopCallback(function () {
        if (!isNull(this.executor)) {
            this.executor.stop();
        }
    }.bind(this));

    return scriptView.scriptPanel;
};
ScriptController.prototype._updateScriptConfig = function (scriptConfig) {
    var oldConfig = this.scriptConfig;
    this.scriptConfig = scriptConfig;

    if (isNull(oldConfig)) {
        this._fillView(this.parentPanel, scriptConfig);
        this._setParameters(this.scriptConfig.parameters);
    } else {
        var oldParameters = toDict(oldConfig.parameters, 'name');
        var newParameters = toDict(scriptConfig.parameters, 'name');

        var controller = this;

        forEachKeyValue(oldParameters, function (name, parameter) {
            if (name in newParameters) {
                return;
            }

            controller._removeParameter(name);
        });

        forEachKeyValue(newParameters, function (name, parameter) {
            if (name in oldParameters) {
                controller._updateParameter(parameter);
            } else {
                controller._addParameter(parameter);
            }
        });

        this.parametersModel.$nextTick(function () {
            var parameterValues = controller.parametersModel.state.parameterValues;
            forEachKeyValue(parameterValues, function (key, value) {
                controller._sendCurrentValue(key, value);
            });
        });
    }
};

ScriptController.prototype.destroy = function () {
    if (!isNull(this.scriptView)) {
        this.scriptView.destroy();
    }
    this.scriptView = null;

    if (!isNull(this.websocket)) {
        this.websocket.close();
    }

    this._stopLogPublisher();

    if (!isNull(this.executor)) {
        this.executor.removeListener(this.executorListener);
    }
};

ScriptController.prototype.setExecutor = function (executor) {
    this.executor = executor;

    this._setParameterValues(executor.parameterValues);

    this.scriptView.setExecuting();
    this._updateViewWithExecutor(executor);
};

ScriptController.prototype._updateViewWithExecutor = function (executor) {
    this._startLogPublisher();

    this.executorListener = {
        'onExecutionStop': function () {
            this._publishLogs();
            this._stopLogPublisher();

            this.scriptView.setStopEnabled(false);
            this.scriptView.setExecutionEnabled(true);

            this.scriptView.hideInputField();
        }.bind(this),

        'onInputPrompt': function (promptText) {
            this.scriptView.showInputField(promptText, function (inputText) {
                executor.sendUserInput(inputText);
            });
        }.bind(this),

        'onFileCreated': function (url, filename) {
            this.scriptView.addFileLink(url, filename);
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
        this.scriptView.setLog('');
    }

    for (; this.logLastIndex < logChunks.length; this.logLastIndex++) {
        var logIndex = this.logLastIndex;

        var logChunk = logChunks[logIndex];

        var text = logChunk.text;
        var textColor = logChunk.text_color;
        var backgroundColor = logChunk.background_color;
        var textStyles = logChunk.text_styles;

        if (toBoolean(logChunk.replace)) {
            this.scriptView.replaceLog(text, textColor, backgroundColor, textStyles, logChunk.custom_position.x, logChunk.custom_position.y);
        } else {
            this.scriptView.appendLog(text, textColor, backgroundColor, textStyles);
        }
    }
};

ScriptController.prototype._initParametersModel = function () {
    var controller = this;

    var sentValues = {};

    this.parametersModel = new Vue({
        data: function () {
            return {
                state:
                    {
                        parameters: [],
                        parameterValues: {}
                    }
            };
        },
        watch: {
            'state.parameterValues': {
                deep: true,
                handler(newValues, oldValues) {
                    var parameterErrors = controller.scriptView.getParameterErrors();

                    forEachKeyValue(newValues, function (key, value) {
                        if (!isEmptyString(parameterErrors[key])) {
                            return;
                        }

                        if (sentValues[key] !== value) {
                            controller._sendCurrentValue(key, value);
                            sentValues[key] = value;
                        }
                    });
                }
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


ScriptController.prototype._preprocessParameter = function (parameter) {
    parameter.multiselect = (parameter.type === 'multiselect');
    if (parameter.type === 'file_upload') {
        parameter.default = null;
    }
};

ScriptController.prototype._setParameters = function (parameters) {
    var parameterValues = {};

    for (var i = 0; i < parameters.length; i++) {
        var parameter = parameters[i];

        this._preprocessParameter(parameter);

        if (!isNull(parameter.default)) {
            parameterValues[parameter.name] = parameter.default;
        } else {
            parameterValues[parameter.name] = null;
        }
    }

    this.parametersModel.state.parameters = parameters;
    this.parametersModel.state.parameterValues = parameterValues;
};

ScriptController.prototype._updateParameter = function (parameter) {
    var foundIndex = -1;

    var parameters = this.parametersModel.state.parameters;

    for (var i = 0; i < parameters.length; i++) {
        var anotherParam = parameters[i];
        if (anotherParam['name'] === parameter['name']) {
            foundIndex = i;
            break;
        }
    }

    if (foundIndex < 0) {
        console.log('Failed to find parameter ' + parameter['name']);
        return;
    }

    this._preprocessParameter(parameter);
    Vue.set(parameters, foundIndex, parameter);
};

ScriptController.prototype._addParameter = function (parameter) {
    this._preprocessParameter(parameter);

    this.parametersModel.state.parameters.push(parameter);
};

ScriptController.prototype._removeParameter = function (parameterName) {
    var foundIndex = -1;

    var parameters = this.parametersModel.state.parameters;

    for (var i = 0; i < parameters.length; i++) {
        var parameter = parameters[i];

        if (parameter['name'] === parameterName) {
            foundIndex = i;
            break;
        }
    }

    if (foundIndex < 0) {
        console.log('Failed to find parameter ' + parameter['name']);
        return;
    }

    parameters.splice(foundIndex, 1);
};

ScriptController.prototype.setParameterValues = function (values) {
    this._setParameterValues(values);
};

ScriptController.prototype._setParameterValues = function (values) {
    for (var i = 0; i < this.parametersModel.state.parameters.length; i++) {
        var parameter = this.parametersModel.state.parameters[i];
        var parameterName = parameter.name;

        var value = values[parameterName];

        if (!isNull(value)) {
            if (!isNull(parameter.values_dependencies)
                && (parameter.values_dependencies.length > 0)
                && (!contains(parameter.values, value))) {
                parameter.values = [value];
            }

            this.parametersModel.state.parameterValues[parameterName] = value;
        } else {
            this.parametersModel.state.parameterValues[parameterName] = null;
        }
    }
};
