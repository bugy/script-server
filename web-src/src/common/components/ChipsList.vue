<template>
  <v-combobox
      ref="field"
      :label="title"
      :model-value="modelValue"
      :search="searchText"
      chips
      class="chips-list"
      closable-chips
      hide-no-data
      multiple
      @update:model-value="onChipsChanged"
      @update:search="onTextInput"/>
</template>

<script>
// Vuetify migration: v-combobox (multiple + chips + closable-chips) replaces
// M.Chips. Typing Enter adds a chip, the chip's cross removes it — both come
// with the component. The CSV behaviours below are untouched business logic:
// typing an unescaped comma commits the finished segments as chips (keeping
// the trailing fragment in the input), losing focus commits whatever is
// typed, and `\,` escapes a comma inside a value.
import clone from 'lodash/clone';

export default {
  name: 'ChipsList',
  emits: ['update:modelValue', 'error'],
  props: {
    modelValue: {
      type: Array,
      default: () => []
    },
    title: {
      type: String,
      default: ''
    }
  },

  data() {
    return {
      searchText: ''
    }
  },

  methods: {
    nativeInput() {
      return this.$refs.field?.$el?.querySelector('input') ?? null;
    },

    // The search prop may keep the same value across a commit (e.g. '' before
    // typing and '' after committing), in which case Vue won't rewrite the
    // user-typed text in the DOM input — sync it explicitly.
    _syncNativeInput() {
      this.$nextTick(() => {
        const input = this.nativeInput();
        if (input && (input.value !== this.searchText)) {
          input.value = this.searchText;
        }
      });
    },

    onChipsChanged(newChips) {
      // Chips committed by the combobox itself (Enter key, or focus loss —
      // VCombobox commits the pending text on blur) carry the raw typed
      // text: trim it and unescape `\,`. Pre-existing chips are kept as-is,
      // a legitimate value may contain a comma.
      const normalized = newChips.map(chip => {
        if (this.modelValue.includes(chip)) {
          return chip;
        }
        return chip.trim().replace(/\\,/g, ',');
      });
      this.$emit('update:modelValue', normalized);
    },

    onTextInput(text) {
      this.searchText = text ?? '';

      const rawValues = this._getRawCsvValues(this.searchText)
      if (!rawValues || rawValues.length < 2) {
        return
      }

      const lastElement = rawValues.pop()

      const newValues = this._parseRawCsvValues(rawValues)
      this._addValues(newValues)

      this.searchText = lastElement
      this._syncNativeInput()
    },

    _getRawCsvValues(inputValue) {
      inputValue = inputValue?.trim()
      if (!inputValue) {
        return
      }

      return inputValue.split(/(?<!\\),/g)
    },

    _parseRawCsvValues(rawValues) {
      return rawValues
          .filter(v => !!v)
          .map(v => v.trim())
          .map(v => v.replace(/\\,/g, ','))
    },

    _addValues(newValues) {
      if (newValues.length < 1) {
        return
      }

      const mergedValues = clone(this.modelValue).concat(newValues)
      this.$emit('update:modelValue', mergedValues);
    }
  }
}
</script>

<style scoped>

</style>
