<template>
  <div :data-error="error" :title="config.description" class="input-field textfield">
    <input :id="id"
           ref="textField"
           :autocomplete="autofillName"
           :disabled="disabled"
           :required="config.required"
           :type="fieldType"
           :value="value"
           :class="{validate : !disabled, autocomplete: autocomplete}"
           @input="inputFieldChanged"/>
    <label :for="id" v-bind:class="{ active: labelActive }">{{ config.name }}</label>
  </div>
</template>

<script>
import '@/common/materializecss/imports/input-fields';
import '@/common/materializecss/imports/autocomplete';
import {isBlankString, isEmptyString, isNull} from '@/common/utils/common';

export default {
  name: 'Textfield',
  props: {
    'value': [String, Number],
    'config': Object,
    disabled: {
      type: Boolean,
      default: false
    }
  },

  data: function () {
    return {
      error: '',
      id: null,
      autocompleteWrapper: null
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

    labelActive() {
      if (!isEmptyString(this.value)) {
        return true;
      }

      var textField = this.$refs.textField;
      if (!isNull(textField) && (textField === document.activeElement)) {
        return true;
      }

      return false;
    },

    autocomplete() {
      return this.config.type === 'editable_list'
    },

    autofillName() {
      return this.config?.name?.replace(/\s+/, '-')
    }
  },

  mounted: function () {
    this.inputFieldChanged();
    this.id = this._uid;

    if (this.autocomplete) {
      this.autocompleteWrapper = M.Autocomplete.init(this.$refs.textField, {minLength: 0})
      this.updateAutocompleteData()

      this.$refs.textField.addEventListener('change', () => this.inputFieldChanged())
    }
  },

  beforeDestroy: function () {
    if (this.autocompleteWrapper) {
      this.autocompleteWrapper.destroy();
    }
  },

  watch: {
    'value': {
      immediate: true,
      handler(newValue) {
        var textField = this.$refs.textField;

        if (!isNull(textField) && (textField.value === newValue)) {
          this._doValidation(this.value);
        } else {
          this.$nextTick(function () {
            if (this.$refs.textField) {
              this._doValidation(this.value);
            }
          }.bind(this));
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
    },
    'config.values': {
      immediate: true,
      handler() {
        if (this.autocompleteWrapper) {
          this.updateAutocompleteData()
        }
      }
    }
  },

  methods: {
    inputFieldChanged() {
      var textField = this.$refs.textField;
      var value = textField.value;

      this._doValidation(value);
      this.$emit('input', value);
    },

    getValidationError(value, textField) {
      if (this.disabled) {
        return '';
      }

      const empty = isBlankString(value);

      if ((textField.validity.badInput)) {
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
      const textField = this.$refs.textField;
      this.error = this.getValidationError(value, textField);
      textField.setCustomValidity(this.error);

      this.$emit('error', this.error);
    },

    triggerRevalidationOnWatch() {
      this.$nextTick(() => {
        if (this.$refs.textField) {
          this._doValidation(this.value);
          M.validate_field(cash(this.$refs.textField));
        }
      });
    },

    updateAutocompleteData() {
      const data = Object.assign({}, ...this.config.values.map((x) => ({[x]: null})))
      this.autocompleteWrapper.updateData(data)
    },

    focus() {
      this.$refs.textField.focus()
      this.triggerRevalidationOnWatch()
    }
  }
}

function getValidByTypeError(value, type, min, max, max_length, regex) {
  if (type === 'text') {
    if (regex) {
        let regexPattern = new RegExp(regex.pattern);
        let matchFound = regexPattern.test(value);
        if (!matchFound) {
          return regex.description
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