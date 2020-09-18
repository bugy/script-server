<template>
    <label :title="config.description" class="input-field checkbox">
        <input :id="config.name"
               type="checkbox"
               :checked="boolValue"
               @input="emitValueChange"
               ref="checkbox"/>
        <span>{{ config.name }}</span>
    </label>
</template>

<script>
    import {toBoolean} from '@/common/utils/common';

    export default {
        props: {
            'value': {
                type: [Boolean, String, Number]
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
        },

        watch: {
            value: {
                immediate: true,
                handler() {
                    this.$nextTick(() => {
                        if (this.value !== this.boolValue) {
                            this.emitValueChange();
                        }
                    });
                }
            }
        }
    }
</script>