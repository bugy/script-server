<template>
  <div :class="{ headless: !showHeaderInModal}" class="input-field date-picker">
    <input :id="id"
           ref="datePicker"
           :placeholder="label"
           class="validate datepicker"
           type="text">
    <label :for="id">{{ label || '' }}</label>
  </div>
</template>

<script>
import {getElementsByTagNameRecursive, isNull, uuidv4} from "@/common/utils/common";
import '@/common/materializecss/imports/datepicker'

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
      id: null
    }
  },
  mounted: function () {
    this.id = 'datepicker_' + uuidv4();

    const datepicker = M.Datepicker.init(this.$refs.datePicker, {
      defaultTime: 'now',
      autoClose: true,
      defaultDate: this.modelValue,
      setDefaultDate: true,
      minDate: new Date(),
      firstDay: 1,
      yearRange: 5,
      onSelect: newDate => {
        if (newDate.getTime() === this.modelValue.getTime()) {
          return;
        }

        this.$nextTick(() => this.$emit('update:modelValue', newDate));
      },
      onDraw: () => {
        const svgs = getElementsByTagNameRecursive(datepicker.$el[0].parentNode, 'svg');
        svgs.forEach(svg => svg.style.fill = 'var(--font-color-main)')
      }
    });
  },
  beforeUnmount: function () {
    const instance = M.Datepicker.getInstance(this.$refs.datePicker);
    instance.destroy();
  },
  watch: {
    'modelValue': {
      immediate: true,
      handler(newValue) {
        if (isNull(this.$refs.datePicker)) {
          return;
        }

        const instance = M.Datepicker.getInstance(this.$refs.datePicker);
        instance.setDate(newValue);
      }
    }
  }
}
</script>

<style scoped>
.date-picker.headless :deep(.datepicker-date-display) {
  display: none;
}
</style>