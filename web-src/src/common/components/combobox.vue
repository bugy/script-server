<template>
  <component
      :is="searchEnabled ? 'v-autocomplete' : 'v-select'"
      ref="field"
      :class="{loading: loading}"
      :data-error="error"
      :disabled="disabled || (options.length === 0) || loading"
      :error-messages="errorMessages"
      :items="items"
      :label="config.name"
      :loading="loading"
      :model-value="selectedValue"
      :multiple="config.multiselect"
      :persistent-placeholder="showHeader"
      :placeholder="placeholder"
      :required="config.required"
      :title="config.description"
      class="combobox"
      @update:model-value="onUserInput"/>
</template>

<script>
// Vuetify migration: v-select (or v-autocomplete when the option list is
// long enough to need filtering — replacing the materialize in-dropdown
// ComboboxSearch) renders the dropdown; all the materialize FormSelect
// plumbing (rebuildCombobox, manual DOM sync, onchange subscription) is
// gone. The value/validation logic below (_fixValueByAllowedValues,
// _validate, forceValue with disabled obsolete options) is untouched
// business logic. External contract preserved: config/modelValue/disabled/
// forceValue/showHeader props, update:modelValue + error emits, data-error.
// The dropdownContainer prop is accepted but unused: Vuetify menus are
// teleported overlays positioned by the framework.
import {contains, isEmptyArray, isEmptyString, isNull} from '@/common/utils/common';

export default {
  name: 'Combobox',
  emits: ['update:modelValue', 'error'],
  props: {
    'config': Object,
    'modelValue': [String, Array],
    'disabled': {
      type: Boolean,
      default: false
    },
    'forceValue': {
      type: Boolean,
      default: false
    },
    dropdownContainer: null,
    showHeader: {
      type: Boolean,
      default: true
    }
  },

  data: function () {
    return {
      options: [],
      anythingSelected: false,
      error: ''
    }
  },

  computed: {
    searchEnabled() {
      return !this.disabled && (this.options.length > 10);
    },

    loading() {
      return this.config.loading
    },

    items() {
      return this.options.map(option => ({
        title: option.value,
        value: option.value,
        props: {disabled: !!option.disabled, title: option.value}
      }));
    },

    selectedValue() {
      if (this.config.multiselect) {
        return this.asArray(this.modelValue);
      }
      return isEmptyString(this.modelValue) ? null : this.modelValue;
    },

    placeholder() {
      if (!this.showHeader) {
        return undefined;
      }
      return this.config.multiselect ? 'Choose your options' : 'Choose your option';
    },

    errorMessages() {
      return isEmptyString(this.error) ? [] : [this.error];
    }
  },

  watch: {
    'config.values': {
      immediate: true,
      handler(newOptionValues) {
        this.setNewOptions(newOptionValues)
      }
    },
    'forceValue': {
      immediate: true,
      handler() {
        this.setNewOptions(this.config.values)
      }
    },

    'modelValue': {
      immediate: true,
      handler(newValue) {
        if (!this._fixValueByAllowedValues(this.config.values)) {
          this._selectValue(newValue);
        }
      }
    }
  },

  methods: {
    onUserInput(value) {
      if (this.config.multiselect) {
        // materialize parity: changing the selection drops forced obsolete
        // values (they were emitted filtered out of the selectedOptions)
        const disabledValues = this.options.filter(o => o.disabled).map(o => o.value);
        value = this.asArray(value).filter(v => !contains(disabledValues, v));
      } else if (isNull(value)) {
        value = null;
      }
      this.emitValueChange(value);
    },

    emitValueChange(value) {
      this._validate(this.asArray(value));
      this.$emit('update:modelValue', value);
    },

    _fixValueByAllowedValues(allowedValues) {
      if (isNull(this.modelValue) || (this.modelValue === '') || (this.modelValue === []) || (this.forceValue)) {
        return false;
      }

      var newValue;
      if (this.config.multiselect) {
        if (!Array.isArray(this.modelValue)) {
          if (contains(allowedValues, this.modelValue)) {
            newValue = [this.modelValue];
          } else {
            newValue = [];
          }

        } else {
          newValue = [];
          for (var i = 0; i < this.modelValue.length; i++) {
            var valueElement = this.modelValue[i];
            if (contains(allowedValues, valueElement)) {
              newValue.push(valueElement)
            }
          }

          if (newValue.length === this.modelValue.length) {
            return false;
          }
        }
      } else {
        if (contains(allowedValues, this.modelValue)) {
          return false;
        }

        newValue = null;
      }

      this.emitValueChange(newValue);
      return true;
    },

    _selectValue(value) {
      const selectedValues = this.asArray(value);

      this.anythingSelected = false;

      for (var i = 0; i < this.options.length; i++) {
        var option = this.options[i];
        option.selected = contains(selectedValues, option.value);

        if (option.selected) {
          this.anythingSelected = true;
        }
      }

      this._validate(selectedValues);
    },

    _validate(selectedValues) {
      if (this.config.required && (selectedValues.length === 0)) {
        this.error = 'required';

      } else {
        const wrongValues = selectedValues.filter(value => !this.config.values.includes(value))
        if (!isEmptyArray(wrongValues)) {
          if (selectedValues.length === 1) {
            this.error = 'Obsolete value'
          } else {
            this.error = 'Obsolete values: ' + wrongValues.join(',')
          }
        } else {
          this.error = ''
        }
      }

      this.$emit('error', this.error);
    },

    setNewOptions(newOptionValues) {
      if (isNull(newOptionValues)) {
        this.options = []
        return
      }

      const newOptions = []
      for (let i = 0; i < newOptionValues.length; i++) {
        newOptions.push({
          value: newOptionValues[i],
          selected: false
        })
      }

      if ((this.forceValue) && !isEmptyString(this.modelValue) && !isEmptyArray(this.modelValue)) {
        const valueAsArray = this.asArray(this.modelValue)
        const disabledOptions = []
        for (const valueElement of valueAsArray) {
          if (!newOptionValues.includes(valueElement)) {
            disabledOptions.push({
              value: valueElement,
              selected: false,
              disabled: true
            })
          }
        }
        newOptions.unshift(...disabledOptions)
      }

      this.options = newOptions

      if (!this._fixValueByAllowedValues(this.config.values)) {
        this._selectValue(this.modelValue)
      }
    },

    asArray(value) {
      var valuesArray = value;

      if (isEmptyString(valuesArray)) {
        valuesArray = [];
      } else if (!Array.isArray(valuesArray)) {
        valuesArray = [valuesArray];
      }
      return valuesArray;
    }
  }
}
</script>

<style scoped>

</style>
