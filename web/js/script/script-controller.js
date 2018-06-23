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
}

ScriptController.prototype.fillView = function (parent) {
    var scriptView = new ScriptView(parent);
    this.scriptView = scriptView;

    scriptView.setScriptDescription(this.scriptConfig.description);
    scriptView.createParameters(this.scriptConfig.parameters);

    scriptView.setExecutionCallback(function (parameterValues) {
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
