function FileUpload(name, description, required) {
    AbstractInput.call(this);

    this.name = name;
    this.required = required;
    this.description = description;

    var fileFieldContainer = createTemplateElement('file_upload-field-template');

    var fileField = $(fileFieldContainer).find('input').get(0);
    this.field = fileField;
    this.field.id = name;

    $(fileFieldContainer).find('label').attr('for', name);

    var captionLabel = $(fileFieldContainer).find('.file_upload-field-label').get(0);
    captionLabel.innerText = name;
    this.captionLabel = captionLabel;

    var valueLabel = $(fileFieldContainer).find('.file_upload-field-value').get(0);
    this.valueLabel = valueLabel;

    this.field.onchange = function () {
        var files = fileField.files;
        if (files && (files.length > 0)) {
            this._setValue(files[0]);
        } else {
            this._setValue(null);
        }
    }.bind(this);

    if (this.required) {
        this.field.setAttribute('required', '');
    }

    if (!isEmptyString(description)) {
        valueLabel.title = description;
    }

    var uploadButton = $(fileFieldContainer).find('a').get(0);
    uploadButton.onclick = function () {
        fileField.click();
    };

    fileField.onfocus = this._reactivateLabel.bind(this);
    fileField.onblur = this._reactivateLabel.bind(this);

    this.panel = fileFieldContainer;

    this._setValue(null);
}


FileUpload.prototype = new AbstractInput();

FileUpload.prototype.getValue = function () {
    return this.value;
};

FileUpload.prototype.setValue = function (value) {
    this._setValue(value);
};

FileUpload.prototype._setValue = function (file) {
    this.value = file;

    if (!isNull(file)) {
        this.valueLabel.innerText = file.name;
    } else {
        this.valueLabel.innerText = '';
    }

    this._reactivateLabel();
    this.validate();
};

FileUpload.prototype._reactivateLabel = function () {
    var focused = this.field === document.activeElement;

    if (!isNull(this.value) || focused) {
        addClass(this.captionLabel, 'active');
    } else {
        removeClass(this.captionLabel, 'active');
    }
};

FileUpload.prototype.getValidationError = function () {
    var value = this.getValue();
    var empty = isNull(value);

    if (this.required && empty) {
        return 'required';
    }

    return '';
};

FileUpload.prototype.validate = function () {
    if (this.isValid()) {
        this.field.setCustomValidity('');
        this.panel.removeAttribute('data-error');
    } else {
        var error = this.getValidationError();
        this.field.setCustomValidity(error);
        this.panel.setAttribute('data-error', error);
    }
};
