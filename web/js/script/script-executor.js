function ScriptExecutor(scriptConfig, scriptName) {
    this.scriptConfig = scriptConfig;
    this.scriptName = scriptName;
    this.parameterValues = null;
    this.websocket = null;
    this.processId = null;
    this.logElements = [];
    this.listeners = [];
    this.inputPromtText = null;
    this.files = [];
}

ScriptExecutor.prototype.start = function (parameterValues) {
    this.parameterValues = parameterValues;

    var callParameters = [];
    parameterValues.each(function (parameter, value) {
        callParameters.push({
            name: parameter,
            value: value
        });
    });
    var callBody = {
        script: this.scriptConfig.name,
        parameters: callParameters
    };

    this.processId = authorizedCallHttp('scripts/execute', callBody, 'POST');
    this._startExecution(this.processId);
};

ScriptExecutor.prototype._startExecution = function (processId) {
    var location = window.location;

    var https = location.protocol.toLowerCase() === 'https:';
    var wsProtocol = https ? 'wss' : 'ws';
    var hostUrl = wsProtocol + '://' + location.host;

    var dir = location.pathname.substring(0, location.pathname.lastIndexOf('/'));
    if (dir) {
        hostUrl += '/' + dir;
    }

    this.websocket = new WebSocket(hostUrl + '/scripts/execute/io/' + processId);

    this.websocket.addEventListener('message', function (message) {
        var event = JSON.parse(message.data);

        var eventType = event.event;
        var data = event.data;

        if (eventType === 'output') {
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

            this.logElements.push(outputElement);

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

    this.websocket.addEventListener('close', function () {
        this.listeners.forEach(function (listener) {
            if (listener.onExecutionStop) {
                listener.onExecutionStop(this);
            }
        }.bind(this));
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
    var processId = this.processId;
    authorizedCallHttp('scripts/execute/stop', {'processId': processId}, 'POST');
};

ScriptExecutor.prototype.abort = function () {
    this.stop();

    if (!this.isFinished()) {
        this.websocket.close();
    }
};
