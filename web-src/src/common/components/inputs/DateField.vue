<template>
  <div :data-error="error" :title="config.description" class="input-field date-field">
    <input :id="id"
           ref="dateInput"
           :disabled="disabled"
           :required="config.required"
           type="date"
           :value="value"
           :class="{validate: !disabled}"
           @change="inputChanged"/>
    <label :for="id" :class="{active: !!value}">{{ config.name }}</label>
  </div>
</template>

<script>
import {isNull} from '@/common/utils/common';

export default {
  name: 'DateField',
  props: {
    value: {
      type: String,
      default: null
    },
    config: {
      type: Object
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      error: '',
      id: null
    }
  },

  mounted() {
    this.id = this._uid;
    this.validate(this.value);
  },

  watch: {
    value(newValue) {
      this.validate(newValue);
    }
  },

  methods: {
    inputChanged() {
      const value = this.$refs.dateInput.value || null;
      this.validate(value);
      this.$emit('input', value);
    },

    validate(value) {
      if (this.disabled) {
        this.error = '';
        this.$emit('error', '');
        return;
      }

      if (isNull(value) || value === '') {
        if (this.config.required) {
          this.error = 'required';
          this.$emit('error', this.error);
        } else {
          this.error = '';
          this.$emit('error', '');
        }
        return;
      }

      this.error = '';
      this.$emit('error', '');
    }
  }
}
</script>

<style scoped>
.date-field input[type=date] {
  height: 1.5em;
  line-height: 1.5em;
}
</style>
