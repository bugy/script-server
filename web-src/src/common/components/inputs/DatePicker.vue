<template>
  <v-date-input
      :first-day-of-week="1"
      :label="label"
      :min="minDate"
      :model-value="modelValue"
      class="date-picker"
      prepend-icon=""
      @update:model-value="onDateChanged"/>
</template>

<script>
// Vuetify migration: v-date-input (text field + calendar menu) replaces the
// materialize M.Datepicker modal. Same constraints as before: dates start
// today (minDate), weeks start on Monday, and the value is only emitted when
// the picked date actually changed. The showHeaderInModal prop is kept for
// compatibility: the v-date-input calendar has no modal header at all
// (hide-header defaults to true), which matches the old headless rendering.
export default {
  name: "DatePicker",
  emits: ['update:modelValue'],
  props: {
    label: {
      type: String
    },
    modelValue: {
      type: Date
    },
    showHeaderInModal: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      minDate: new Date()
    }
  },
  methods: {
    onDateChanged(newDate) {
      if (newDate && this.modelValue && (newDate.getTime() === this.modelValue.getTime())) {
        return;
      }

      this.$emit('update:modelValue', newDate);
    }
  }
}
</script>

<style scoped>

</style>
