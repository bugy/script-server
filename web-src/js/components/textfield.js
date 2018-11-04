import Vue from 'vue';
import {isEmptyString, isNull} from '../common';

(function () {
    Vue.component('textfield', {
        template:
            '<div class="input-field" :title="config.description" :data-error="error">\n'
            + '  <input :id="config.name" '
            + '     :type="fieldType" '
            + '     :value="value" '
            + '     :required="config.required" '
            + '     class="validate" '
            + '     @input="inputFieldChanged"'
            + '     ref="textField"/>\n'
            + '  <label :for="config.name" v-bind:class="{ active: labelActive }">{{ config.name }}</label>\n'
            + '</div>',

        props: {
            'value': [String, Number],
            'config': Object
        },

        data: function () {
            return {
                error: ''
            }
        },

        computed: {
            fieldType() {
                if (this.config.type === 'int') {
                    return 'number';
                } else if (this.config.secure) {
                    return 'password';
                }

                return 'text';
            },

            labelActive() {
                if (!isEmptyString(this.value)) {
                    return true;
                }

                var textField = this.$refs.textField;
                if (!isNull(textField) && (textField === document.activeElement)) {
                    return true;
                }

                return false;
            }
        },

        mounted: function () {
            this.inputFieldChanged();
        },

        watch: {
            'value': {
                immediate: true,
                handler(newValue) {
                    var textField = this.$refs.textField;

                    if (!isNull(textField) && (textField.value === newValue)) {
                        this._doValidation(this.value);
                    } else {
                        this.$nextTick(function () {
                            this._doValidation(this.value);
                        }.bind(this));
                    }
                }
            }
        },

        methods: {
            inputFieldChanged() {
                var textField = this.$refs.textField;
                var value = textField.value;

                this._doValidation(value);
                this.$emit('input', value);
            },

            getValidationError(value, textField) {
                var empty = isEmptyString(value) || isEmptyString(value.trim());

                if ((textField.validity.badInput)) {
                    return getInvalidTypeError(this.type);
                }

                if (this.config.required && empty) {
                    return 'required';
                }

                if (!empty) {
                    var typeError = getValidByTypeError(value, this.config.type, this.config.min, this.config.max);
                    if (!isEmptyString(typeError)) {
                        return typeError;
                    }
                }

                return '';
            },

            _doValidation(value) {
                var textField = this.$refs.textField;
                this.error = this.getValidationError(value, textField);
                textField.setCustomValidity(this.error);

                this.$emit('error', this.error);
            }
        }
    });

    function getValidByTypeError(value, type, min, max) {
        if (type === 'int') {
            var isInteger = /^(((\-?[1-9])(\d*))|0)$/.test(value);
            if (!isInteger) {
                return getInvalidTypeError(type);
            }

            var intValue = parseInt(value);

            var minMaxValid = true;
            var minMaxError = "";
            if (!isNull(min)) {
                minMaxError += "min: " + min;

                if (intValue < parseInt(min)) {
                    minMaxValid = false;
                }
            }

            if (!isNull(max)) {
                if (intValue > parseInt(max)) {
                    minMaxValid = false;
                }

                if (!isEmptyString(minMaxError)) {
                    minMaxError += ", ";
                }

                minMaxError += "max: " + max;
            }

            if (!minMaxValid) {
                return minMaxError;
            }

            return "";
        }

        return "";
    }

    function getInvalidTypeError(type) {
        if (type === 'int') {
            return "integer expected";
        }

        return type + " expected";
    }
}());