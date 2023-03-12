<template>
  <label :title="config.description" class="input-field checkbox">
    <input :id="config.name"
           ref="checkbox"
           :checked="boolValue"
           type="checkbox"
           :disabled="disabled"
           @input="emitValueChange"/>
    <span>{{ config.name }}</span>
  </label>
</template>

<script>
import {isNull, toBoolean} from '@/common/utils/common';

export default {
  props: {
    'value': {
      type: [Boolean, String, Number]
    },
    'config': Object,
    'disabled': {
      type: [Boolean]
    }
  },

  computed: {
    boolValue() {
      return toBoolean(this.value);
    }
  },

  mounted: function () {
    this.$refs.checkbox.indeterminate = isNull(this.value)
    this.emitValueChange();
  },

  methods: {
    emitValueChange() {
      if (this.$refs.checkbox.indeterminate) {
        this.$emit('input', undefined);
        return;
      }

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