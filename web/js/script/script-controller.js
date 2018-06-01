function ScriptController(scriptConfig, executionStartCallback) {
    this.scriptConfig = scriptConfig;
    this.scriptName = scriptConfig.name;
    this.executionStartCallback = executionStartCallback;
    this.scriptView = null;

    this.logPublisher = null;
    this.logLastIndex = 0;
    this.executor = null;
    this.executorListener = null;
}

ScriptController.prototype.fillView = function (parent) {
    var scriptView = new ScriptView(parent);
    this.scriptView = scriptView;

    scriptView.setScriptDescription(this.scriptConfig.description);
    scriptView.createParameters(this.scriptConfig.parameters);

    scriptView.executeButtonCallback = function () {
        this.scriptView.setExecuting();
        scriptView.setLog('Calling the script...');

        try {
            var parameterValues = {};
            scriptView.parameterControls.each(function (parameter, control) {
                var value = control.getValue();
                if (!isNull(value)) {
                    parameterValues[parameter.name] = value;
                }
            });

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
                scriptView.appendLogElement(document.createTextNode(errorLogElement));
            }
        }
    }.bind(this);

    scriptView.stopButtonCallback = function () {
        if (!isNull(this.executor)) {
            this.executor.stop();
        }
    }.bind(this);

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

    this.scriptView.setParameterValues(executor.parameterValues);

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

    var logElements = this.executor.logElements;

    if ((this.logLastIndex === 0) && (logElements.length > 0)) {
        this.scriptView.setLog('');
    }

    for (; this.logLastIndex < logElements.length; this.logLastIndex++) {
        var logIndex = this.logLastIndex;
        this.scriptView.appendLogElement(logElements[logIndex]);
    }
};
