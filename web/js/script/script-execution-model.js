"use strict";

function ScriptExecutor(scriptConfig) {
    this.scriptConfig = scriptConfig;
    this.scriptName = scriptConfig.name;
    this.parameterValues = null;
    this.websocket = null;
    this.executionId = null;
    this.logChunks = [];
    this.listeners = [];
    this.inputPromtText = null;
    this.files = [];
}

ScriptExecutor.prototype.start = function (parameterValues) {
    this.parameterValues = parameterValues;

    var formData = new FormData();
    formData.append('__script_name', this.scriptConfig.name);

    forEachKeyValue(parameterValues, function (parameter, value) {
        formData.append(parameter, value);
    });

    this.executionId = authorizedCallHttp('scripts/execution', formData, 'POST');
    this._startExecution(this.executionId);
};

ScriptExecutor.prototype._startExecution = function (executionId) {
    var location = window.location;

    var https = location.protocol.toLowerCase() === 'https:';
    var wsProtocol = https ? 'wss' : 'ws';
    var hostUrl = wsProtocol + '://' + location.host;

    var dir = getUrlDir();
    if (dir) {
        hostUrl += '/' + dir;
    }

    this.websocket = new WebSocket(hostUrl + '/scripts/execution/io/' + executionId);

    this.websocket.addEventListener('message', function (message) {
        var event = JSON.parse(message.data);

        var eventType = event.event;
        var data = event.data;

        if (eventType === 'output') {
            this.logChunks.push(data);

        } else if (eventType === 'input') {
            this.inputPromtText = data;

            this.listeners.forEach(function (listener) {
                if (listener.onInputPrompt) {
                    listener.onInputPrompt(data);
                }
            });


        } else if (eventType === 'file') {
            this.files.push({
                'url': data.url,
                'filename': data.filename
            });

            this.listeners.forEach(function (listener) {
                if (listener.onFileCreated) {
                    listener.onFileCreated(data.url, data.filename)
                }
            });
        }
    }.bind(this));

    this.websocket.addEventListener('close', function (event) {
        var executionFinished = (event.code === 1000);
        try {
            this.listeners.forEach(function (listener) {
                if (listener.onExecutionStop) {
                    listener.onExecutionStop(this);
                }
            }.bind(this));

        } finally {
            if (!executionFinished) {
                authorizedCallHttp('scripts/execution/status/' + executionId, null, 'GET', function (response) {
                    if (response === 'finished') {
                        authorizedCallHttp('scripts/execution/cleanup/' + executionId, null, 'POST');
                    }
                });

            } else {
                authorizedCallHttp('scripts/execution/cleanup/' + executionId, null, 'POST');
            }
        }
    }.bind(this));
};

ScriptExecutor.prototype.addListener = function (listener) {
    this.listeners.push(listener);

    if (!isNull(this.inputPromtText)) {
        if (listener.onInputPrompt) {
            listener.onInputPrompt(this.inputPromtText);
        }
    }

    if (this.isFinished()) {
        if (listener.onExecutionStop) {
            listener.onExecutionStop(this);
        }
    }

    if (this.files.length > 0) {
        this.files.forEach(function (fileDescriptor) {
            this.listeners.forEach(function (listener) {
                if (listener.onFileCreated) {
                    listener.onFileCreated(fileDescriptor.url, fileDescriptor.filename)
                }
            });
        }.bind(this));
    }
};

ScriptExecutor.prototype.removeListener = function (listener) {
    removeElement(this.listeners, listener);
};

ScriptExecutor.prototype.sendUserInput = function (inputText) {
    if (!this.isFinished()) {
        this.websocket.send(inputText);
    }
};

ScriptExecutor.prototype.isFinished = function () {
    if (isNull(this.websocket)) {
        return true;
    }

    return ((this.websocket.readyState === 2) || (this.websocket.readyState === 3));
};

ScriptExecutor.prototype.stop = function () {
    var executionId = this.executionId;
    authorizedCallHttp('scripts/execution/stop/' + executionId, null, 'POST');
};

ScriptExecutor.prototype.abort = function () {
    this.stop();

    if (!this.isFinished()) {
        this.websocket.close();
    }
};

function restoreExecutor(executionId, callback) {
    var dataContainer = {rawConfig: null, rawValues: null};
    var loadHandler = function () {
        if (isNull(dataContainer.rawValues) || isNull(dataContainer.rawConfig)) {
            return;
        }

        var scriptConfig = JSON.parse(dataContainer.rawConfig);
        var parameterValues = JSON.parse(dataContainer.rawValues);

        var executor = new ScriptExecutor(scriptConfig);
        executor.executionId = executionId;
        executor.parameterValues = parameterValues;
        executor._startExecution(executionId);

        callback(executor);
    };

    authorizedCallHttp('scripts/execution/config/' + executionId, null, 'GET', function (rawConfig) {
        dataContainer.rawConfig = rawConfig;
        loadHandler();
    });

    authorizedCallHttp('scripts/execution/values/' + executionId, null, 'GET', function (rawValues) {
        dataContainer.rawValues = rawValues;
        loadHandler();
    });

}