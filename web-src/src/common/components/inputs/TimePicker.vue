<template>
    <div :data-error="error" class="time-picker input-field">
        <input :id="id"
               :placeholder="label"
               :required="required"
               @input="inputFieldChanged"
               class="validate"
               ref="timePicker"
               type="text">
        <label :for="id">{{label || ''}}</label>
    </div>
</template>

<script>
    import {isEmptyString, isNull, uuidv4} from "@/common/utils/common";

    export default {
        name: 'TimePicker',
        props: {
            label: {
                type: String
            },
            value: {
                type: String
            },
            required: {
                type: Boolean,
                default: true
            }
        },
        data() {
            return {
                id: null,
                error: ''
            }
        },
        mounted: function () {
            this.id = 'timepicker_' + uuidv4();

            this.$refs.timePicker.value = this.value;
            M.updateTextFields();
        },
        watch: {
            'value': {
                immediate: true,
                handler(newValue) {
                    if (isNull(this.$refs.timePicker)) {
                        return;
                    }

                    this.$refs.timePicker.value = newValue;

                    this.doValidation(newValue);
                }
            },
            'error': {
                handler(error) {
                    this.$refs.timePicker.setCustomValidity(error);
                    M.validate_field(cash(this.$refs.timePicker));
                    this.$emit('error', error);
                }
            }
        },
        methods: {
            doValidation: function (value) {
                const trimmedValue = value.trim();

                if (this.required && (trimmedValue === '')) {
                    this.error = 'required';
                } else if (!isEmptyString(trimmedValue)
                    && !trimmedValue.match(/^((0?[0-9])|(1[0-9])|(2[0-3])):[0-5][0-9]$/)) {
                    this.error = 'Format HH:MM';
                } else {
                    this.error = '';
                }
            },

            inputFieldChanged() {
                const textField = this.$refs.timePicker;
                const value = textField.value;

                const trimmedValue = value.trim();
                this.doValidation(trimmedValue);

                if (isEmptyString(this.error)) {
                    this.$emit('input', trimmedValue);
                }
            }
        },

    }
</script>

<style scoped>

</style>