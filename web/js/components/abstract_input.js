function AbstractInput() {
    this.panel = document.createElement("div");
    addClass(this.panel, "input-field");
    addClass(this.panel, "inline");
}

AbstractInput.prototype = new Component();

AbstractInput.prototype.getElement = function () {
    return this.panel;
};

AbstractInput.prototype.getValue = function () {

};

AbstractInput.prototype.isValid = function () {
    return isEmptyString(this.getValidationError());
};

AbstractInput.prototype.getValidationError = function () {
    return "";
};