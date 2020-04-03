<template>
    <div :data-error="error" :title="config.description" class="input-field">
        <textarea
                :id="elementId"
                :required="config.required"
                :value="value"
                @input="textAreaChanged"
                class="materialize-textarea"
                ref="textArea"
                type="text">

        </textarea>
        <label :for="elementId">{{config.name}}</label>
    </div>
</template>

<script>
    import {isBlankString, isNull} from '@/common/utils/common';

    export default {
        name: 'TextArea',

        props: {
            'value': [String],
            'config': Object
        },

        data() {
            return {
                error: ''
            }
        },

        mounted: function () {
            this.textAreaChanged();
        },

        watch: {
            'value': {
                immediate: true,
                handler(newValue) {
                    const textArea = this.$refs.textArea;
                    const notificationAfterTextAreaChanged = !isNull(textArea) && textArea.value === newValue;

                    if (!isNull(textArea) && notificationAfterTextAreaChanged) {
                        this.doValidation(newValue);
                    } else {
                        this.$nextTick(() => {
                            if (this.$refs.textArea) {
                                this.doValidation(newValue);

                                if (!notificationAfterTextAreaChanged) {
                                    this.initTextArea();
                                }
                            }
                        });
                    }
                }
            }
        },

        computed: {
            elementId() {
                return this._uid;
            }
        },

        methods: {
            textAreaChanged() {
                const textArea = this.$refs.textArea;
                const value = textArea.value;

                this.doValidation(value);
                this.$emit('input', value);
            },

            initTextArea() {
                M.textareaAutoResize(this.$refs.textArea);
                M.updateTextFields();
            },

            doValidation(value) {
                const textArea = this.$refs.textArea;
                this.error = this.getValidationError(value);
                textArea.setCustomValidity(this.error);

                this.$emit('error', this.error);
            },

            getValidationError(value) {
                const empty = isBlankString(value);

                if (this.config.required && empty) {
                    return 'required';
                }

                return '';
            }

        }
    }
</script>

<style scoped>

</style>