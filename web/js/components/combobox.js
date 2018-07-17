'use strict';

function Combobox(name, defaultValue, required, values, description, multiple) {
    AbstractInput.call(this);

    this.required = required;
    this.multiple = multiple;

    var label = document.createElement("label");
    label.innerText = name;
    label.setAttribute("for", name);


    this.selectField = document.createElement("select");
    this.selectField.id = name;
    addClass(this.selectField, "validate");
    if (required) {
        this.selectField.setAttribute("required", "");
    }
    if (multiple) {
        this.selectField.setAttribute('multiple', '');
    }

    var selectOption = document.createElement("option");
    selectOption.setAttribute("disabled", "");
    selectOption.setAttribute("value", "");
    selectOption.innerHTML = "Choose your option";
    this.selectField.appendChild(selectOption);

    for (var i = 0; i < values.length; i++) {
        var value = values[i];

        var valueOption = document.createElement("option");
        valueOption.innerHTML = value;
        valueOption.setAttribute("value", value);
        this.selectField.appendChild(valueOption);
    }

    this._setValueInternal(defaultValue);

    this.selectField.onchange = $.proxy(this.validate, this);

    this.panel.appendChild(this.selectField);
    this.panel.appendChild(label);
    if (!isEmptyString(description)) {
        this.panel.title = description;
    }
}

Combobox.prototype = new AbstractInput();

Combobox.prototype.getValue = function () {
    return this._getValueInternal();
};

Combobox.prototype._getValueInternal = function () {
    if (this.multiple) {
        return $(this.selectField).val();
    } else {
        return this.selectField.value;
    }
};

Combobox.prototype.setValue = function (value) {
    $(this.selectField).children('option').removeAttr('selected');

    this._setValueInternal(value);

    $(this.selectField).material_select();
};

Combobox.prototype._setValueInternal = function (value) {
    var foundMatching = false;
    if (!isNull(value)) {
        if (this.multiple && Array.isArray(value)) {
            $(this.selectField).children('option').each(function () {
                if (contains(value, this.value)) {
                    $(this).prop('selected', true);
                    foundMatching = true;
                }
            });
        } else {
            var matchingChildren = $(this.selectField).children('option[value="' + value + '"]');
            if (matchingChildren.size() === 1) {
                matchingChildren.prop('selected', true);
                foundMatching = true;
            }
        }
    }

    if (!foundMatching) {
        $(this.selectField).children('option[value=""][disabled]').attr('selected', '');
    }

    this.validate();
};

Combobox.prototype.getValidationError = function () {
    var empty;
    if (this.multiple) {
        var value = this._getValueInternal();
        empty = isEmptyString(value) || (value.length <= 0);
    } else {
        empty = this.selectField.validity.valueMissing;
    }

    if (this.required && empty) {
        return "required";
    }

    return "";
};

Combobox.prototype.onAdd = function () {
    $(this.selectField).material_select();

    var input = findNeighbour(this.selectField, "input");
    input.removeAttribute("readonly"); //otherwise the field will ignore "setCustomValidity"
    input.setAttribute("data-constrainwidth", false);

    $(this.selectField).siblings('ul').children('li').each(function () {
        var text = $(this).children('span:first-child').text();
        if (text) {
            this.title = text;
        }
    });

    this.validate();
};

Combobox.prototype.onDestroy = function () {
    $(this.selectField).material_select('destroy');
};

Combobox.prototype.validate = function () {
    var input = findNeighbour(this.selectField, "input");

    if (this.isValid()) {
        this.panel.removeAttribute("data-error");
        if (!isNull(input)) {
            input.setCustomValidity("");
        }
    } else {
        var error = this.getValidationError();
        this.panel.setAttribute("data-error", error);
        if (!isNull(input)) {
            input.setCustomValidity(error);
        }
    }
};
