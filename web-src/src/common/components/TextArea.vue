<template>
  <div :data-error="error" :title="config.description" class="input-field">
        <textarea
            :id="elementId"
            ref="textArea"
            :required="config.required"
            :value="modelValue"
            class="materialize-textarea"
            type="text"
            @input="textAreaChanged">

        </textarea>
    <label :class="{ active: labelActive }" :for="elementId">{{ config.name }}</label>
  </div>
</template>

<script>
import '@/common/materializecss/imports/input-fields';
import {isBlankString, isEmptyString, isNull} from '@/common/utils/common';

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
    this.textAreaChanged();
  },

  watch: {
    'modelValue': {
      immediate: true,
      handler(newValue) {
        const textArea = this.$refs.textArea;
        const notificationAfterTextAreaChanged = !isNull(textArea) && textArea.value === newValue;

        if (!isNull(textArea) && notificationAfterTextAreaChanged) {
          this.doValidation(newValue);
        } else {
          this.$nextTick(() => {
            if (this.$refs.textArea) {
              this.doValidation(newValue);

              if (!notificationAfterTextAreaChanged) {
                this.initTextArea();
              }
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
    elementId() {
      return this.$.uid;
    },

    labelActive() {
      if (!isEmptyString(this.modelValue)) {
        return true;
      }

      var textArea = this.$refs.textArea;
      if (!isNull(textArea) && (textArea === document.activeElement)) {
        return true;
      }

      return false;
    },
  },

  methods: {
    textAreaChanged() {
      const textArea = this.$refs.textArea;
      const value = textArea.value;

      this.doValidation(value);
      this.$emit('update:modelValue', value);
    },

    initTextArea() {
      M.textareaAutoResize(this.$refs.textArea);
      M.updateTextFields();
    },

    doValidation(value) {
      const textArea = this.$refs.textArea;
      this.error = this.getValidationError(value);
      textArea.setCustomValidity(this.error);

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