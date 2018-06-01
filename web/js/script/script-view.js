function ScriptView(parent) {
    this.parameterControls = new Hashtable();

    this.scriptPanel = createTemplateElement('script-panel-template');
    this.scriptPanel.id = 'script-panel-' + guid(8);

    parent.appendChild(this.scriptPanel);

    this.logPanel = this.scriptPanel.getElementsByClassName('log-panel')[0];
    this.logContent = this.scriptPanel.getElementsByClassName('log-content')[0];
    this.inputPanel = this.scriptPanel.getElementsByClassName('script-input-panel')[0];
    this.validationPanel = this.scriptPanel.getElementsByClassName('validation-panel')[0];
    this.validationErrorsList = this.scriptPanel.getElementsByClassName('validation-errors-list')[0];
    this.scriptDescription = this.scriptPanel.getElementsByClassName('script-description')[0];
    this.stopButton = this.scriptPanel.getElementsByClassName('button-stop')[0];
    this.executeButton = this.scriptPanel.getElementsByClassName('button-execute')[0];
    this.paramsPanel = this.scriptPanel.getElementsByClassName('script-parameters-panel')[0];
    this.filesDownloadPanel = this.scriptPanel.getElementsByClassName('files-download-panel')[0];
    this.inputLabel = this.inputPanel.getElementsByClassName('script-input-label')[0];
    this.inputField = this.inputPanel.getElementsByClassName('script-input-field')[0];

    bindTemplatedFieldLabel(this.inputField, this.inputLabel);

    this._initLogPanel();
    this._initExecuteButton();
    this._initStopButton();

    hide(this.validationPanel);

    show(this.stopButton);
    show(this.executeButton);
    setButtonEnabled(this.executeButton, true);
    setButtonEnabled(this.stopButton, false);

    hide(this.logPanel);
    hide(this.inputPanel);
    hide(this.filesDownloadPanel);
}

ScriptView.prototype.setScriptDescription = function (description) {
    if (!isNull(description)) {
        show(this.scriptDescription);
        this.scriptDescription.innerText = description;
    } else {
        hide(this.scriptDescription);
    }
};

ScriptView.prototype.createParameters = function (parameters) {
    if (isNull(parameters) || (parameters.length === 0)) {
        hide(this.paramsPanel);
        return;
    }

    parameters.forEach(function (parameter) {
        var control = createParameterControl(parameter);
        this.parameterControls.put(parameter, control);

        var element = control.getElement();
        addClass(element, 'parameter');

        this.paramsPanel.appendChild(element);
        control.onAdd();
    }.bind(this));

    show(this.paramsPanel);
};

ScriptView.prototype.setParameterValues = function (parameterValues) {
    this.parameterControls.each(function (parameter, control) {
        var value = parameterValues[parameter.name];
        if (!isNull(value)) {
            control.setValue(value);
        } else {
            control.setValue(null);
        }
    });
};

ScriptView.prototype._initLogPanel = function () {
    var logPanel = this.logPanel;
    var logContent = this.logContent;
    var shadow = logPanel.getElementsByClassName('log-panel-shadow')[0];

    hide(logPanel);

    var wasBottom = true;
    var scrollStyleUpdate = function () {
        var isTop = logContent.scrollTop === 0;
        var isBottom = (logContent.scrollTop + logContent.clientHeight + 5) > (logContent.scrollHeight);

        var shadowTop = !isTop;
        var shadowBottom = !isBottom;

        if (shadowTop && shadowBottom) {
            addClass(shadow, 'shadow-top-bottom');
            removeClass(shadow, 'shadow-top');
            removeClass(shadow, 'shadow-bottom');
        } else if (shadowTop) {
            removeClass(shadow, 'shadow-top-bottom');
            addClass(shadow, 'shadow-top');
            removeClass(shadow, 'shadow-bottom');
        } else if (shadowBottom) {
            removeClass(shadow, 'shadow-top-bottom');
            removeClass(shadow, 'shadow-top');
            addClass(shadow, 'shadow-bottom');
        } else {
            removeClass(shadow, 'shadow-top-bottom');
            removeClass(shadow, 'shadow-top');
            removeClass(shadow, 'shadow-bottom');
        }

        wasBottom = isBottom;
    };
    logContent.addEventListener('scroll', scrollStyleUpdate);

    var mouseDown = false;
    logContent.addEventListener('mousedown', function () {
        mouseDown = true;
    });

    logContent.addEventListener('mouseup', function () {
        mouseDown = false;
    });

    var updateScroll = function () {
        if ((wasBottom) && (!mouseDown)) {
            logContent.scrollTop = logContent.scrollHeight;
        } else {
            scrollStyleUpdate();
        }
    };

    //noinspection JSUnresolvedVariable
    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
    var observer = new MutationObserver(updateScroll);

    window.addEventListener('resize', function () {
        updateScroll([]);
    });

    var config = {childList: true, attributes: false, characterData: true, subtree: true};
    observer.observe(logContent, config);
};

ScriptView.prototype.destroy = function () {
    this.parameterControls.each(function (parameter, control) {
        control.onDestroy();
    });
};

ScriptView.prototype._initStopButton = function () {
    this.stopButton.addEventListener('click', function () {
        this.stopButtonCallback();
    }.bind(this));
};

ScriptView.prototype.executeButtonCallback = function () {

};

ScriptView.prototype.stopButtonCallback = function () {

};

ScriptView.prototype._initExecuteButton = function () {
    var executeButton = this.executeButton;
    var logPanel = this.logPanel;
    var errorsPanel = this.validationPanel;
    var errorsList = this.validationErrorsList;
    var filesDownloadPanel = this.filesDownloadPanel;
    var parameterControls = this.parameterControls;

    executeButton.addEventListener('click', function () {
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
            show(errorsPanel);

            for (var parameter in errors) {
                var errorLabel = document.createElement('li');
                errorLabel.innerText = parameter + ': ' + errors[parameter];
                errorsList.appendChild(errorLabel);
            }

            hide(logPanel);
            return;
        }

        this.executeButtonCallback();

    }.bind(this));
};

ScriptView.prototype.setExecutionEnabled = function (enabled) {
    setButtonEnabled(this.executeButton, enabled);
};

ScriptView.prototype.setStopEnabled = function (enabled) {
    setButtonEnabled(this.stopButton, enabled);
};

ScriptView.prototype.setLog = function (text) {
    this.logContent.innerText = text;
};

ScriptView.prototype.appendLogElement = function (logElement) {
    this.logContent.appendChild(logElement);
};

ScriptView.prototype.setExecuting = function () {
    setButtonEnabled(this.executeButton, false);
    setButtonEnabled(this.stopButton, true);

    hide(this.validationPanel);
    show(this.logPanel);
};

ScriptView.prototype.showInputField = function (promptText, userInputCallback) {
    this.inputLabel.innerText = promptText;

    this.inputField.value = '';

    this.inputField.onkeyup = function (event) {
        if (event.keyCode === 13) {
            userInputCallback(this.inputField.value);

            this.inputField.value = '';
        }
    }.bind(this);

    show(this.inputPanel);
    this.inputField.focus();
};

ScriptView.prototype.hideInputField = function () {
    this.inputLabel.innerText = '';
    this.inputField.value = '';
    this.inputField.onkeyup = null;
    hide(this.inputPanel);
};

ScriptView.prototype.addFileLink = function (url, filename) {
    show(this.filesDownloadPanel);

    var downloadLink = document.createElement('a');
    addClass(downloadLink, 'waves-effect');
    addClass(downloadLink, 'waves-teal');
    addClass(downloadLink, 'btn-flat');
    downloadLink.setAttribute('download', filename);
    downloadLink.href = url;
    downloadLink.target = '_blank';
    downloadLink.appendChild(document.createTextNode(filename));

    var downloadImage = document.createElement('img');
    downloadImage.src = 'images/file_download.png';
    downloadLink.appendChild(downloadImage);

    this.filesDownloadPanel.appendChild(downloadLink);
};

