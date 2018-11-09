import Vue from 'vue'
import {toBoolean} from '../common';

(function () {
    Vue.component('checkbox', {
        template:
            '<label class="input-field" :title="config.description">\n'
            + '  <input :id="config.name" '
            + '     type="checkbox" '
            + '     :checked="boolValue" '
            + '     @input="emitValueChange"'
            + '     ref="checkbox"/>\n'
            + '  <span>{{ config.name }}</span>\n'
            + '</label>',

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