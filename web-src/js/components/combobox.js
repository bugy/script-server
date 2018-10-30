'use strict';

(function () {
    Vue.component('combobox', {
        template:
            '<div class="input-field" :title="config.description" :data-error="error">\n'
            + '  <select '
            + '     :id="config.name" '
            + '     ref="selectField" '
            + '     class="validate" '
            + '     :required="config.required"'
            + '     :multiple="config.multiselect"'
            + '     :disabled="options.length === 0">\n'
            + '    <option :selected="!anythingSelected" value="" disabled>Choose your option</option>\n'
            + '    <option v-for="option in options" :value="option.value" :selected="option.selected">{{ option.value }}</option>\n'
            + '  </select>'
            + '  <label :for="config.name">{{ config.name }}</label>\n'
            + '</div>',

        props: {
            'config': Object,
            'value': [String, Array]
        },

        data: function () {
            return {
                options: [],
                anythingSelected: false,
                error: ''
            }
        },

        watch: {
            'config.values': {
                immediate: true,
                handler(newOptionValues) {
                    if (isNull(newOptionValues)) {
                        this.options = [];
                        return;
                    }

                    var newOptions = [];
                    for (var i = 0; i < newOptionValues.length; i++) {
                        newOptions.push({
                            value: newOptionValues[i],
                            selected: false
                        });
                    }

                    this.options = newOptions;
                    if (!this._fixValueByAllowedValues(this.config.values)) {
                        this._selectValue(this.value);

                        this.$nextTick(function () {
                            this.rerenderCombobox();
                        }.bind(this));
                    }
                }
            },

            'value': {
                immediate: true,
                handler(newValue) {
                    if (!this._fixValueByAllowedValues(this.config.values)) {
                        this._selectValue(newValue);
                    }
                }
            }
        },

        mounted: function () {
            // for some reason subscription in template (i.e. @change="..." doesn't work for select input)
            $(this.$refs.selectField).on('change', function () {
                var value;
                if (this.config.multiselect) {
                    value = $(this.$refs.selectField).val();
                } else {
                    value = this.$refs.selectField.value;
                }
                this.emitValueChange(value);
            }.bind(this));

            this.rerenderCombobox();

            this.$watch('error', function (errorValue) {
                var inputField = findNeighbour(this.$refs.selectField, 'input');
                if (!isNull(inputField)) {
                    inputField.setCustomValidity(errorValue);
                }
            }, {
                immediate: true
            })
        },

        destroyed: function () {
            $(this.$refs.selectField).material_select('destroy');
        },

        methods: {
            emitValueChange(value) {
                this._validate(asArray(value));
                this.$emit('input', value);
            },

            _fixValueByAllowedValues(allowedValues) {
                if (isNull(this.value) || (this.value === '') || (this.value === [])) {
                    return false;
                }

                var newValue;
                if (this.config.multiselect) {
                    if (!Array.isArray(this.value)) {
                        if (contains(allowedValues, this.value)) {
                            return false;
                        }
                        newValue = [this.value];
                    } else {
                        newValue = [];
                        for (var i = 0; i < this.value.length; i++) {
                            var valueElement = this.value[i];
                            if (contains(allowedValues, valueElement)) {
                                newValue.push(valueElement)
                            }
                        }

                        if (newValue.length === this.value.length) {
                            return false;
                        }
                    }
                } else {
                    if (contains(allowedValues, this.value)) {
                        return false;
                    }

                    newValue = null;
                }

                this.emitValueChange(newValue);
                return true;
            },

            _selectValue(value) {
                var selectedValues = asArray(value);

                this.anythingSelected = false;

                var existingSelectedValues = new Set();

                for (var i = 0; i < this.options.length; i++) {
                    var option = this.options[i];
                    option.selected = contains(selectedValues, option.value);

                    if (option.selected) {
                        this.anythingSelected = true;
                        existingSelectedValues.add(option.value);
                    }
                }

                this._validate(selectedValues);

                var requiresReRender = true;

                if (this.config.multiselect) {
                    var comboboxValues = $(this.$refs.selectField).val();
                    // rerendering combobox during selection closes popup, so we need to avoid it
                    requiresReRender = !arraysEqual(comboboxValues, selectedValues);
                }

                if (requiresReRender) {
                    this.$nextTick(function () {
                        this.rerenderCombobox();
                    }.bind(this));
                }
            },

            _validate(selectedValues) {
                if (this.config.required && (selectedValues.length === 0)) {
                    this.error = 'required';
                } else {
                    this.error = '';
                }
                this.$emit('error', this.error);
            },

            rerenderCombobox() {
                $(this.$refs.selectField).material_select();

                var inputField = findNeighbour(this.$refs.selectField, 'input');

                inputField.removeAttribute('readonly'); // otherwise the field will ignore "setCustomValidity"
                inputField.setAttribute('data-constrainwidth', false);

                $(this.$refs.selectField).siblings('ul').children('li').each(function () {
                    var text = $(this).children('span:first-child').text();
                    if (text) {
                        this.title = text;
                    }
                });

                inputField.setCustomValidity(this.error);
            }
        }
    });

    function asArray(value) {
        var valuesArray = value;

        if (isEmptyString(valuesArray)) {
            valuesArray = [];
        } else if (!Array.isArray(valuesArray)) {
            valuesArray = [valuesArray];
        }
        return valuesArray;
    }
}());
