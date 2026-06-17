<template>
  <v-textarea
      ref="field"
      :data-error="error"
      :error-messages="errorMessages"
      :label="config.name"
      :model-value="modelValue"
      :required="config.required"
      :title="config.description"
      auto-grow
      class="textarea-field"
      rows="1"
      @update:model-value="onValueChanged"/>
</template>

<script>
// Vuetify migration: only the rendering layer changed (v-textarea with
// auto-grow replacing the materialize textarea + M.textareaAutoResize).
// The validation logic below is untouched business logic. External contract
// preserved: modelValue/config props, update:modelValue + error emits,
// data-error attribute.
import {isBlankString, isNull} from '@/common/utils/common';

export default {
  name: 'TextArea',

  emits: ['update:modelValue', 'error'],
  props: {
    'modelValue': [String],
    'config': Object
  },

  data() {
    return {
      error: ''
    }
  },

  mounted: function () {
    this.onValueChanged(this.nativeTextarea()?.value ?? this.modelValue ?? '');
  },

  watch: {
    'modelValue': {
      immediate: true,
      handler(newValue) {
        const textArea = this.nativeTextarea();

        if (!isNull(textArea) && (textArea.value === newValue)) {
          this.doValidation(newValue);
        } else {
          this.$nextTick(() => {
            if (this.nativeTextarea()) {
              this.doValidation(newValue);
            }
          });
        }
      }
    },
    'config.max_length'() {
      this.doValidation(this.modelValue)
    }
  },

  computed: {
    errorMessages() {
      return this.error ? [this.error] : [];
    }
  },

  methods: {
    nativeTextarea() {
      return this.$refs.field?.$el?.querySelector('textarea') ?? null;
    },

    onValueChanged(value) {
      if (isNull(value)) {
        value = '';
      }

      this.doValidation(value);
      this.$emit('update:modelValue', value);
    },

    doValidation(value) {
      this.error = this.getValidationError(value);
      this.nativeTextarea()?.setCustomValidity(this.error ?? '');

      this.$emit('error', this.error);
    },

    getValidationError(value) {
      const empty = isBlankString(value);

      if (this.config.required && empty) {
        return 'required';
      }

      if (this.config.max_length && (value.length > this.config.max_length)) {
        return 'Max chars allowed: ' + this.config.max_length
      }

      return null;
    }

  }
}
</script>

<style scoped>

</style>
