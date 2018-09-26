'use strict';

(function () {
    Vue.component('checkbox', {
        template:
            '<div class="input-field" :title="config.description">\n'
            + '  <input :id="config.name" '
            + '     type="checkbox" '
            + '     :checked="boolValue" '
            + '     @input="emitValueChange"'
            + '     ref="checkbox"/>\n'
            + '  <label :for="config.name">{{ config.name }}</label>\n'
            + '</div>',

        props: {
            'value': [Boolean, String, Number],
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
                this.$emit('input', this.$refs.checkbox.checked)
            }
        }
    });
}());