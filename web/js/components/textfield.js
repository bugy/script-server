function TextField(name, defaultValue, required, type, min, max, description) {
    AbstractInput.call(this);

    this.required = required;
    this.type = type;
    this.min = min;
    this.max = max;

    var label = document.createElement("label");
    label.innerText = name;
    label.setAttribute("for", name);

    this.field = document.createElement("input");
    this.field.id = name;
    this.field.type = "text";

    if (!isNull(this.type)) {
        if (this.type == "int") {
            this.field.type = "number";
        }
    }

    if (!isNull(defaultValue)) {
        addClass(label, "active");
        this.field.value = defaultValue;
    }

    if (this.required) {
        this.field.setAttribute("required", "");
    }

    addClass(this.field, "validate");

    this.field.oninput = $.proxy(this.validate, this);
    this.validate();

    this.panel.appendChild(this.field);
    this.panel.appendChild(label);
    this.panel.title = description;
}

TextField.prototype = new AbstractInput();

TextField.prototype.getValue = function () {
    return this.field.value;
};

TextField.prototype.getValidationError = function () {
    var value = this.getValue();
    var empty = isEmptyString(value) || isEmptyString(value.trim());

    if ((this.field.validity.badInput)) {
        return getInvalidTypeError(this.type);
    }

    if (this.required && empty) {
        return "required";
    }

    if (!empty) {
        var typeError = getValidByTypeError(value, this.type, this.min, this.max);
        if (!isEmptyString(typeError)) {
            return typeError;
        }
    }

    return "";
};

TextField.prototype.validate = function () {
    if (this.isValid()) {
        this.field.setCustomValidity("");
        this.panel.removeAttribute("data-error");
    } else {
        var error = this.getValidationError();
        this.field.setCustomValidity(error);
        this.panel.setAttribute("data-error", error);
    }
};
