<template>
    <div class="input-field file-upload-field" :title="config.description" :data-error="error">
        <a class="btn-flat waves-effect btn-floating" ref="uploadButton">
            <i class="material-icons">file_upload</i>
        </a>
        <input :id="config.name"
               type="file"
               :required="config.required"
               class="validate"
               @input="updateValue"
               @blur="focused = false"
               @focus="focused = true"
               ref="fileField"/>
        <label class="file-upload-field-label" :for="config.name" v-bind:class="{ active: (value || focused) }">
            {{ config.name }}</label>
        <label class="file-upload-field-value" :for="config.name">{{ valueText }}</label>
        <label></label>
    </div>
</template>

<script>
    import {isNull} from '../common';

    export default {
        props: {
            'value': [File],
            'config': Object
        },

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
    }
</script>

<style scoped>
    input[type=file] {
        position: absolute;
        left: -9999px;
        opacity: 0;
    }

    .btn-flat {
        position: absolute;
        top: -8px;
        right: -8px;
    }

    .btn-flat > i {
        color: #9e9e9e;
        clip-path: inset(0 0 14px 0);
    }

    label {
        cursor: pointer;
    }

    .file-upload-field-value {
        position: relative;
        display: block;
        width: 100%;
        padding-right: 24px;

        overflow: hidden;
        text-overflow: ellipsis;

        /* same as text field */
        border-bottom: 1px solid #9e9e9e;
        height: 1.5rem;
        color: inherit;
    }

    input[type="file"]:focus + * + .file-upload-field-value {
        border-bottom: 1px solid #26a69a;
        box-shadow: 0 1px 0 0 #26a69a;
    }

    input[type="file"]:focus + .file-upload-field-label {
        color: #26a69a;
    }

    input[type="file"]:invalid + * + .file-upload-field-value {
        border-bottom: 1px solid #e51c23;
        box-shadow: 0 1px 0 0 #e51c23;
    }
</style>