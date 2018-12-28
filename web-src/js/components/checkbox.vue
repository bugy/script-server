<template>
    <label class="input-field" :title="config.description">
        <input :id="config.name"
               type="checkbox"
               :checked="boolValue"
               @input="emitValueChange"
               ref="checkbox"/>
        <span>{{ config.name }}</span>
    </label>
</template>

<script>
    import {toBoolean} from '../common';

    export default {
        props: {
            'value': {
                type: [Boolean, String, Number],
                default: false
            },
            'config': Object
        },

        computed: {
            boolValue() {
                return toBoolean(this.value);
            }
        },

        mounted: function () {
            this.emitValueChange();
        },

        methods: {
            emitValueChange() {
                this.$emit('input', this.$refs.checkbox.checked);
            }
        }
    }
</script>