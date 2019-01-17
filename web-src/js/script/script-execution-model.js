import {forEachKeyValue, getWebsocketUrl, isNull, isWebsocketClosed, removeElement} from '../common';
import {authorizedCallHttp} from '../index';

export function ScriptExecutor(scriptName) {
    this.scriptName = scriptName;
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
    formData.append('__script_name', this.scriptName);

    forEachKeyValue(parameterValues, function (parameter, value) {
        if (Array.isArray(value)) {
            for (var i = 0; i < value.length; i++) {
                var valueElement = value[i];
                formData.append(parameter, valueElement);
            }
        } else if (!isNull(value)) {
            formData.append(parameter, value);
        }
    });

    this.executionId = authorizedCallHttp('executions/start', formData, 'POST');
    this._startExecution(this.executionId);
};

ScriptExecutor.prototype._startExecution = function (executionId) {
    this.websocket = new WebSocket(getWebsocketUrl('executions/io/' + executionId));

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
                authorizedCallHttp('executions/status/' + executionId, null, 'GET', function (response) {
                    if (response === 'finished') {
                        authorizedCallHttp('executions/cleanup/' + executionId, null, 'POST');
                    }
                });

            } else {
                authorizedCallHttp('executions/cleanup/' + executionId, null, 'POST');
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

    return isWebsocketClosed(this.websocket);
};

ScriptExecutor.prototype.stop = function () {
    var executionId = this.executionId;
    authorizedCallHttp('executions/stop/' + executionId, null, 'POST');
};

ScriptExecutor.prototype.abort = function () {
    this.stop();

    if (!this.isFinished()) {
        this.websocket.close();
    }
};

export function restoreExecutor(executionId, callback) {
    authorizedCallHttp('executions/config/' + executionId, null, 'GET', function (response) {
        var executionConfig = JSON.parse(response);

        var executor = new ScriptExecutor(executionConfig.scriptName);
        executor.executionId = executionId;
        executor.parameterValues = executionConfig.parameterValues;
        executor._startExecution(executionId);

        callback(executor);
    });
}