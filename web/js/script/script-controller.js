'use strict';

function ScriptController(scriptConfig, executionStartCallback) {
    this.scriptConfig = scriptConfig;
    this.scriptName = scriptConfig.name;
    this.executionStartCallback = executionStartCallback;
    this.scriptView = null;

    this.logPublisher = null;
    this.logLastIndex = 0;
    this.executor = null;
    this.executorListener = null;

    this._initParameters(this.scriptName, this.scriptConfig.parameters);
}

ScriptController.prototype.fillView = function (parent) {
    var scriptView = new ScriptView(parent, this.parametersModel);
    this.scriptView = scriptView;

    scriptView.setScriptDescription(this.scriptConfig.description);

    scriptView.setExecutionCallback(function () {
        var parameterValues = $.extend({}, this.parametersModel.state.parameterValues);

        this.scriptView.setExecuting();
        scriptView.setLog('Calling the script...');

        try {
            this.executor = new ScriptExecutor(this.scriptConfig);
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

ScriptController.prototype.destroy = function () {
    if (!isNull(this.scriptView)) {
        this.scriptView.destroy();
    }
    this.scriptView = null;

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

ScriptController.prototype._initParameters = function (scriptName, parameters) {
    var parameterValues = {};

    var dependantParameters = new Map();

    for (var i = 0; i < parameters.length; i++) {
        var parameter = parameters[i];

        parameter.multiselect = (parameter.type === 'multiselect');
        if (parameter.type === 'file_upload') {
            parameter.default = null;
        }

        if (!isNull(parameter.default)) {
            parameterValues[parameter.name] = parameter.default;
        } else {
            parameterValues[parameter.name] = null;
        }

        if (!isNull(parameter.values_dependencies) && (parameter.values_dependencies.length > 0)) {
            dependantParameters.set(parameter, new Map());
            for (var j = 0; j < parameter.values_dependencies.length; j++) {
                var dependency = parameter.values_dependencies[j];
                dependantParameters.get(parameter).set(dependency, undefined);
            }
        }
    }

    this.parametersModel = new Vue({
        data: function () {
            return {
                state:
                    {
                        parameters: parameters,
                        parameterValues: parameterValues
                    }
            };
        },
        watch: {
            'state.parameterValues': {
                immediate: true,
                deep: true,
                handler(newValues, oldValues) {
                    dependantParameters.forEach(function (dependencies, parameter) {
                        var hasChanges = false;
                        var everythingFilled = true;

                        dependencies.forEach(function (oldValue, dependency) {
                            var newValue = newValues[dependency];

                            if ((typeof oldValue === 'undefined') || (newValue !== oldValue)) {
                                dependencies.set(dependency, newValue);
                                hasChanges = true;
                            }

                            if (isEmptyValue(newValue)) {
                                everythingFilled = false;
                            }
                        });

                        if (!everythingFilled) {
                            if (parameter.values.length > 0) {
                                parameter.values = [];
                            }
                        } else if (hasChanges) {
                            var currentValues = $.extend({}, this.state.parameterValues);

                            var queryParameters = encodeURIComponent(JSON.stringify({
                                'script_name': scriptName,
                                'parameter_name': parameter.name,
                                'current_values': currentValues
                            }));
                            callHttp('scripts/config/parameter-values?query_parameters=' + queryParameters,
                                null,
                                'GET',
                                function (values) {
                                    var dependenciesObsolete = false;
                                    dependencies.forEach(function (oldValue, dependency) {
                                        var currentValue = this.state.parameterValues[dependency];
                                        if (currentValue !== currentValues[dependency]) {
                                            dependenciesObsolete = true;
                                        }
                                    }.bind(this));

                                    if (!dependenciesObsolete) {
                                        parameter.values = JSON.parse(values);
                                    }
                                }.bind(this));
                        }
                    }.bind(this));
                }
            }
        }
    });
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
