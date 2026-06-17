<template>
  <v-checkbox
      :disabled="disabled"
      :indeterminate="indeterminate"
      :label="config.name"
      :model-value="boolValue"
      :title="config.description"
      class="checkbox"
      @update:model-value="checkboxChanged"/>
</template>

<script>
// Pilot component of the materialize -> Vuetify migration: same external API
// as before (modelValue/config/disabled props, update:modelValue emit,
// indeterminate state while modelValue is null, value normalisation on mount).
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

  data() {
    return {
      indeterminate: isNull(this.modelValue)
    }
  },

  computed: {
    boolValue() {
      return toBoolean(this.modelValue);
    }
  },

  mounted: function () {
    if (!this.indeterminate) {
      // normalise string/number values to a boolean, as the old component did
      this.$emit('update:modelValue', this.boolValue);
    }
  },

  methods: {
    checkboxChanged(checked) {
      this.indeterminate = false;
      this.$emit('update:modelValue', !!checked);
    }
  },

  watch: {
    modelValue: {
      immediate: true,
      handler() {
        if (!isNull(this.modelValue)) {
          this.indeterminate = false;
        }

        this.$nextTick(() => {
          if (!isNull(this.modelValue) && (this.modelValue !== this.boolValue)) {
            this.$emit('update:modelValue', this.boolValue);
          }
        });
      }
    }
  }
}
</script>
