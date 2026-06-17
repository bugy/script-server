<template>
  <v-text-field
      ref="field"
      :data-error="error"
      :error-messages="errorMessages"
      :label="label"
      :model-value="text"
      :required="required"
      class="time-picker"
      placeholder="HH:MM"
      @update:model-value="inputFieldChanged"/>
</template>

<script>
// Vuetify migration: v-text-field replaces the materialize input +
// M.updateTextFields / M.validate_field label and validity plumbing. The
// HH:MM validation is untouched business logic: an invalid value shows the
// error and is NOT emitted (the model keeps the last valid time).
import {isEmptyString} from "@/common/utils/common";

export default {
  name: 'TimePicker',
  emits: ['update:modelValue', 'error'],
  props: {
    label: {
      type: String
    },
    modelValue: {
      type: String
    },
    required: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      // What the field displays. Kept separate from modelValue so an invalid
      // typed time stays visible (with its error) instead of snapping back
      // to the last valid value.
      text: this.modelValue ?? '',
      error: ''
    }
  },
  computed: {
    errorMessages() {
      return isEmptyString(this.error) ? [] : [this.error];
    }
  },
  watch: {
    'modelValue': {
      immediate: true,
      handler(newValue) {
        this.text = newValue ?? '';
        this.doValidation(this.text);
      }
    },
    'error': {
      handler(error) {
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

    inputFieldChanged(value) {
      this.text = value ?? '';
      const trimmedValue = this.text.trim();
      this.doValidation(trimmedValue);

      if (isEmptyString(this.error)) {
        this.$emit('update:modelValue', trimmedValue);
      }
    }
  },

}
</script>

<style scoped>

</style>
