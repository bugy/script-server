<template>
    <div class="input-field" :title="config.description" :data-error="error">
        <input :id="config.name"
               :type="fieldType"
               :value="value"
               :required="config.required"
               class="validate"
               @input="inputFieldChanged"
               ref="textField"/>
        <label :for="config.name" v-bind:class="{ active: labelActive }">{{ config.name }}</label>
    </div>
</template>

<script>
    import {isEmptyString, isNull} from '../common';

    export default {
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
                    return getInvalidTypeError(this.config.type);
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
    }

    function getValidByTypeError(value, type, min, max) {
        if (type === 'int') {
            const isInteger = /^(((-?[1-9])(\d*))|0)$/.test(value);
            if (!isInteger) {
                return getInvalidTypeError(type);
            }

            var intValue = parseInt(value);

            var minMaxValid = true;
            var minMaxError = '';
            if (!isNull(min)) {
                minMaxError += 'min: ' + min;

                if (intValue < parseInt(min)) {
                    minMaxValid = false;
                }
            }

            if (!isNull(max)) {
                if (intValue > parseInt(max)) {
                    minMaxValid = false;
                }

                if (!isEmptyString(minMaxError)) {
                    minMaxError += ', ';
                }

                minMaxError += 'max: ' + max;
            }

            if (!minMaxValid) {
                return minMaxError;
            }

            return '';

        } else if (type === 'ip') {
            if (isEmptyString(validateIp4(value)) || isEmptyString(validateIp6(value))) {
                return ''
            }

            return 'IPv4 or IPv6 expected';

        } else if (type === 'ip4') {
            return validateIp4(value);

        } else if (type === 'ip6') {
            return validateIp6(value);
        }

        return '';
    }

    function validateIp4(value) {
        const ipElements = value.trim().split('.');
        if (ipElements.length !== 4) {
            return 'IPv4 expected'
        }

        for (const element of ipElements) {
            if (isEmptyString(element)) {
                return 'Empty IP block'
            }

            if (!/^[12]?[0-9]{1,2}$/.test(element)) {
                return 'Invalid block ' + element;
            }

            const elementNumeric = parseInt(element, 10);
            if (elementNumeric > 255) {
                return 'Out of range ' + elementNumeric;
            }
        }

        return '';
    }

    function validateIp6(value) {
        const chunks = value.trim().split('::');
        if (chunks.length > 2) {
            return ':: allowed only once';
        }

        const elements = [];

        elements.push(...chunks[0].split(':'));
        if (chunks.length === 2) {
            elements.push('::');
            elements.push(...chunks[1].split(':'))
        }

        const hasCompressZeroes = chunks.length === 2;
        let afterDoubleColon = false;
        let hasIp4 = false;
        let count = 0;

        for (const element of elements) {
            if (hasIp4) {
                return 'IPv4 should be the last';
            }

            if (element === '::') {
                afterDoubleColon = true;

            } else if (element.includes('.') && ((afterDoubleColon || count >= 6))) {
                if (!isEmptyString(validateIp4(element))) {
                    return 'Invalid IPv4 block ' + element;
                }
                hasIp4 = true;
                count++;

            } else if (!/^[A-F0-9]{0,4}$/.test(element.toUpperCase())) {
                return 'Invalid block ' + element;
            }

            count++;
        }

        if (((count < 8) && (!hasCompressZeroes)) || (count > 8)) {
            return 'Should be 8 blocks';
        }

        return '';
    }

    function getInvalidTypeError(type) {
        if (type === 'int') {
            return 'integer expected';
        }

        return type + ' expected';
    }
</script>