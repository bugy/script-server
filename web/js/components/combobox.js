function Combobox(name, defaultValue, required, values) {
    AbstractInput.call(this);

    this.required = required;

    var label = document.createElement("label");
    label.innerText = name;
    label.setAttribute("for", name);


    this.selectField = document.createElement("select");
    this.selectField.id = name;
    addClass(this.selectField, "validate");
    if (required) {
        this.selectField.setAttribute("required", "");
    }

    var selectOption = document.createElement("option");
    selectOption.setAttribute("disabled", "");
    selectOption.setAttribute("value", "");
    if (isNull(defaultValue)) {
        selectOption.setAttribute("selected", "");
    }
    selectOption.innerHTML = "Choose your option";
    this.selectField.appendChild(selectOption);

    for (var i = 0; i < values.length; i++) {
        var value = values[i];

        var valueOption = document.createElement("option");
        valueOption.innerHTML = value;
        valueOption.setAttribute("value", value);
        if (!isNull(defaultValue) && defaultValue == value) {
            valueOption.setAttribute("selected", "");
        }
        this.selectField.appendChild(valueOption);
    }

    this.selectField.onchange = $.proxy(this.validate, this);

    this.panel.appendChild(this.selectField);
    this.panel.appendChild(label);
}

Combobox.prototype = new AbstractInput();

Combobox.prototype.getValue = function () {
    return this.selectField.value;
};

Combobox.prototype.getValidationError = function () {
    var empty = this.selectField.validity.valueMissing;

    if (this.required && empty) {
        return "required";
    }

    return "";
};

Combobox.prototype.onAdd = function () {
    $(this.selectField).material_select();

    var input = findNeighbour(this.selectField, "input");
    input.removeAttribute("readonly"); //otherwise the field will ignore "setCustomValidity"

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