'use strict';

(function () {
    Vue.component('file-upload-field', {
        props: {
            'value': [File],
            'config': Object
        },

        template:
            '<div class="input-field file-upload-field" :title="config.description" :data-error="error">\n'
            + '  <a class="btn-flat waves-effect btn-floating" ref="uploadButton">'
            + '    <i class="material-icons">file_upload</i>'
            + '  </a>\n'
            + '  <input :id="config.name" '
            + '     type="file" '
            + '     :required="config.required" '
            + '     class="validate" '
            + '     @input="updateValue"'
            + '     @blur="focused = false"'
            + '     @focus="focused = true"'
            + '     ref="fileField"/>\n'
            + '  <label class="file-upload-field-label" :for="config.name" v-bind:class="{ active: (value || focused) }">'
            + '{{ config.name }}</label>\n'
            + '  <label class="file-upload-field-value" :for="config.name">{{ valueText }}</label>\n'
            + '  <label ></label>\n'
            + '</div>',

        data: function () {
            return {
                error: '',
                focused: false
            }
        },

        computed: {
            valueText() {
                if (isNull(this.value)) {
                    return '';
                }

                return this.value.name;
            },

            fieldType() {
                if (this.config.type === 'int') {
                    return 'number';
                } else if (this.config.secure) {
                    return 'password';
                }

                return 'text';
            }
        },

        mounted: function () {
            this.updateValue();

            var uploadButton = this.$refs.uploadButton;
            var fileField = this.$refs.fileField;
            uploadButton.onclick = function () {
                fileField.click();
            };
        },

        methods: {
            updateValue() {
                var fileField = this.$refs.fileField;

                var files = fileField.files;
                var value;
                if (files && (files.length > 0)) {
                    value = files[0];
                } else {
                    value = null;
                }

                this.error = this.getValidationError(value);
                fileField.setCustomValidity(this.error);

                this.$emit('error', this.error);
                this.$emit('input', value);
            },

            getValidationError(value) {
                var empty = isNull(value);

                if (this.config.required && empty) {
                    return 'required';
                }

                return '';
            }
        }
    });
}());

