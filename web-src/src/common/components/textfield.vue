<template>
  <v-combobox
      v-if="autocomplete"
      ref="field"
      :data-error="error"
      :disabled="disabled"
      :error-messages="errorMessages"
      :hide-no-data="true"
      :items="config.values"
      :label="config.name"
      :model-value="modelValue"
      :required="config.required"
      :title="config.description"
      :type="fieldType"
      class="textfield"
      @update:model-value="onValueChanged"
      @update:search="onValueChanged"/>
  <v-text-field
      v-else
      ref="field"
      :data-error="error"
      :disabled="disabled"
      :error-messages="errorMessages"
      :label="config.name"
      :model-value="modelValue"
      :required="config.required"
      :title="config.description"
      :type="fieldType"
      class="textfield"
      @update:model-value="onValueChanged"/>
</template>

<script>
// Vuetify migration: only the rendering layer changed (v-text-field /
// v-combobox for editable_list autocompletion, replacing the materialize
// input + M.Autocomplete). The whole validation engine below is untouched
// business logic. External contract preserved: modelValue/config/disabled
// props, update:modelValue + error emits, data-error attribute, focus().
import {isBlankString, isEmptyString, isFullRegexMatch, isNull} from '@/common/utils/common';

export default {
  name: 'Textfield',
  emits: ['update:modelValue', 'error'],
  props: {
    'modelValue': [String, Number],
    'config': Object,
    disabled: {
      type: Boolean,
      default: false
    }
  },

  data: function () {
    return {
      error: ''
    }
  },

  computed: {
    fieldType() {
      if (this.config.secure) {
        return 'password';
      } else if (this.config.type === 'int') {
        return 'number';
      }

      return 'text';
    },

    autocomplete() {
      return this.config.type === 'editable_list'
    },

    errorMessages() {
      return isEmptyString(this.error) ? [] : [this.error];
    }
  },

  mounted: function () {
    this.onValueChanged(this.nativeInput()?.value ?? this.modelValue ?? '');
  },

  watch: {
    'modelValue': {
      immediate: true,
      handler(newValue) {
        const input = this.nativeInput();

        if (!isNull(input) && (input.value === newValue)) {
          this._doValidation(this.modelValue);
        } else {
          this.$nextTick(() => {
            if (this.nativeInput()) {
              this._doValidation(this.modelValue);
            }
          });
        }
      }
    },
    'config.required': {
      handler() {
        this.triggerRevalidationOnWatch();
      }
    },
    disabled() {
      this.triggerRevalidationOnWatch();
    },
    'config.min': {
      handler() {
        this.triggerRevalidationOnWatch();
      }
    }
  },

  methods: {
    nativeInput() {
      return this.$refs.field?.$el?.querySelector('input') ?? null;
    },

    onValueChanged(value) {
      if (isNull(value)) {
        value = '';
      }

      this._doValidation(value);
      this.$emit('update:modelValue', value);
    },

    getValidationError(value, textField) {
      if (this.disabled) {
        return '';
      }

      const empty = isBlankString(value);

      if (textField && textField.validity.badInput) {
        return getInvalidTypeError(this.config.type);
      }

      if (this.config.required && empty) {
        return 'required';
      }

      if (!empty) {
        var typeError = getValidByTypeError(value, this.config.type, this.config.min, this.config.max,
            this.config.max_length, this.config.regex);
        if (!isEmptyString(typeError)) {
          return typeError;
        }
      }

      return '';
    },

    _doValidation(value) {
      this.error = this.getValidationError(value, this.nativeInput());

      this.$emit('error', this.error);
    },

    triggerRevalidationOnWatch() {
      this.$nextTick(() => {
        if (this.nativeInput()) {
          this._doValidation(this.modelValue);
        }
      });
    },

    focus() {
      this.$refs.field?.focus();
    }
  }
}

function getValidByTypeError(value, type, min, max, max_length, regex) {
  if (!type || (type === 'text')) {
    if (regex) {
      let matches = isFullRegexMatch(regex.pattern, value);
      if (!matches) {
        if (regex.description) {
          return regex.description
        } else {
          return 'pattern mismatch'
        }
      }
    }
    if (max_length) {
      if (value.length > max_length) {
        return 'Max chars allowed: ' + max_length
      }
    }
  }

  if (type === 'int') {
    const isInteger = /^(((-?[1-9])(\d*))|0)$/.test(value);
    if (!isInteger) {
      return getInvalidTypeError(type);
    }

    var intValue = parseInt(value);

    var minMaxValid = true;
    var minMaxError = '';
    if (!isNull(min)) {
      minMaxError += 'min: ' + min;

      if (intValue < parseInt(min)) {
        minMaxValid = false;
      }
    }

    if (!isNull(max)) {
      if (intValue > parseInt(max)) {
        minMaxValid = false;
      }

      if (!isEmptyString(minMaxError)) {
        minMaxError += ', ';
      }

      minMaxError += 'max: ' + max;
    }

    if (!minMaxValid) {
      return minMaxError;
    }

    return '';

  } else if (type === 'ip') {
    if (isEmptyString(validateIp4(value)) || isEmptyString(validateIp6(value))) {
      return ''
    }

    return 'IPv4 or IPv6 expected';

  } else if (type === 'ip4') {
    return validateIp4(value);

  } else if (type === 'ip6') {
    return validateIp6(value);
  }

  return '';
}

function validateIp4(value) {
  const ipElements = value.trim().split('.');
  if (ipElements.length !== 4) {
    return 'IPv4 expected'
  }

  for (const element of ipElements) {
    if (isEmptyString(element)) {
      return 'Empty IP block'
    }

    if (!/^[12]?[0-9]{1,2}$/.test(element)) {
      return 'Invalid block ' + element;
    }

    const elementNumeric = parseInt(element, 10);
    if (elementNumeric > 255) {
      return 'Out of range ' + elementNumeric;
    }
  }

  return '';
}

function validateIp6(value) {
  const chunks = value.trim().split('::');
  if (chunks.length > 2) {
    return ':: allowed only once';
  }

  const elements = [];

  elements.push(...chunks[0].split(':'));
  if (chunks.length === 2) {
    elements.push('::');
    elements.push(...chunks[1].split(':'))
  }

  const hasCompressZeroes = chunks.length === 2;
  let afterDoubleColon = false;
  let hasIp4 = false;
  let count = 0;

  for (const element of elements) {
    if (hasIp4) {
      return 'IPv4 should be the last';
    }

    if (element === '::') {
      afterDoubleColon = true;

    } else if (element.includes('.') && ((afterDoubleColon || count >= 6))) {
      if (!isEmptyString(validateIp4(element))) {
        return 'Invalid IPv4 block ' + element;
      }
      hasIp4 = true;
      count++;

    } else if (!/^[A-F0-9]{0,4}$/.test(element.toUpperCase())) {
      return 'Invalid block ' + element;
    }

    count++;
  }

  if (((count < 8) && (!hasCompressZeroes)) || (count > 8)) {
    return 'Should be 8 blocks';
  }

  return '';
}

function getInvalidTypeError(type) {
  if (type === 'int') {
    return 'integer expected';
  }

  return type + ' expected';
}
</script>
