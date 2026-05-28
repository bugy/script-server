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
  emits: ['update:modelValue', 'error'],
  props: {
    'modelValue': {
      type: [Boolean, String, Number]
    },
    'config': Object,
    'disabled': {
      type: [Boolean]
    }
  },

  computed: {
    boolValue() {
      return toBoolean(this.modelValue);
    }
  },

  mounted: function () {
    this.$refs.checkbox.indeterminate = isNull(this.modelValue)
    this.emitValueChange();
  },

  methods: {
    emitValueChange() {
      if (this.$refs.checkbox.indeterminate) {
        this.$emit('update:modelValue', undefined);
        return;
      }

      this.$emit('update:modelValue', this.$refs.checkbox.checked);
    }
  },

  watch: {
    modelValue: {
      immediate: true,
      handler() {
        this.$nextTick(() => {
          if (this.modelValue !== this.boolValue) {
            this.emitValueChange();
          }
        });
      }
    }
  }
}
</script>