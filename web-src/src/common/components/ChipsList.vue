<template>
  <div class="chips-list">
    <label>{{ title }}</label>
    <div ref="chips" class="chips" @blur="onFocusLost"></div>
  </div>
</template>

<script>
import '@/common/materializecss/imports/chips';
import {isNull} from '@/common/utils/common';
import clone from 'lodash/clone';

export default {
  name: 'ChipsList',
  props: {
    value: {
      type: Array,
      default: () => []
    },
    title: {
      type: String,
      default: ''
    }
  },

  mounted: function () {
    this.initChips([]);

    const instance = M.Chips.getInstance(this.$refs.chips);
    instance.$input[0].addEventListener('blur', this.onFocusLost);
    instance.$input[0].addEventListener('input', this.onTextInput);
  },

  beforeDestroy: function () {
    const instance = M.Chips.getInstance(this.$refs.chips);
    if (instance) {
      instance.$input[0].removeEventListener('blur', this.onFocusLost);
      instance.$input[0].removeEventListener('input', this.onTextInput);
    }
  },

  watch: {
    value: {
      immediate: true,
      handler(newValue) {
        if (!isNull(this.$refs.chips)) {
          this.updateChips();
        } else {
          this.$nextTick(() => {
            this.updateChips();
          });
        }
      }
    }
  },

  methods: {
    initChips(data) {
      M.Chips.init(this.$refs.chips, {
        data,
        onChipAdd: this.updateValue,
        onChipDelete: this.updateValue
      });
    },

    updateValue() {
      const instance = M.Chips.getInstance(this.$refs.chips);
      this.$emit('input', instance.chipsData.map(d => d.tag));
    },

    updateChips() {
      this.initChips(this.value.map(v => ({tag: v})));
    },

    onFocusLost() {
      const rawValues = this._getRawCsvValuesFromText()
      if (!rawValues) {
        return
      }
      const instance = M.Chips.getInstance(this.$refs.chips);

      instance.$input[0].value = ''
      const newValues = this._parseRawCsvValues(rawValues)
      this._addValues(newValues)
    },

    onTextInput() {
      const rawValues = this._getRawCsvValuesFromText()
      if (!rawValues || rawValues.length < 2) {
        return
      }

      const instance = M.Chips.getInstance(this.$refs.chips);

      const lastElement = rawValues.pop()
      instance.$input[0].value = ''

      const newValues = this._parseRawCsvValues(rawValues)
      this._addValues(newValues)

      this.$nextTick(() => {
        instance.$input[0].focus()
        instance.$input[0].value = lastElement
      })
    },

    _getRawCsvValuesFromText() {
      const instance = M.Chips.getInstance(this.$refs.chips);
      if (!instance) {
        return
      }

      const inputValue = instance.$input[0].value?.trim()
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
      if (newValues.size < 1) {
        return
      }

      const mergedValues = clone(this.value).concat(newValues)
      this.$emit('input', mergedValues);
    }
  }
}
</script>

<style scoped>
.chips-list {
  padding-left: 0.75em;
  padding-right: 0.75em;
  position: relative;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.chips-list .chips.input-field {
  min-height: 3rem;
  margin-top: 0;
  margin-bottom: 8px;
}

.chips-list label {
  position: absolute;
  top: -13px;
}

.chips-list >>> .chip {
  margin-bottom: 3px;
}

</style>