function Checkbox(name, defaultValue, description) {
    AbstractInput.call(this);

    var label = document.createElement("label");
    label.innerText = name;
    label.setAttribute("for", name);

    this.checkBox = document.createElement("input");
    this.checkBox.id = name;
    this.checkBox.type = "checkbox";

    if (!isNull(defaultValue)) {
        this.checkBox.checked = defaultValue;
    }

    this.panel.appendChild(this.checkBox);
    this.panel.appendChild(label);
    if (!isEmptyString(description)) {
        this.panel.title = description;
    }
}

Checkbox.prototype = new AbstractInput();

Checkbox.prototype.getValue = function () {
    return this.checkBox.checked;
};
