<template>
    <div :class="{ headless: !showHeaderInModal}" class="input-field date-picker">
        <input :id="id"
               :placeholder="label"
               class="validate datepicker"
               ref="datePicker"
               type="text">
        <label :for="id">{{label || ''}}</label>
    </div>
</template>

<script>
import {isNull, uuidv4} from "@/common/utils/common";
import '@/common/materializecss/imports/datepicker'

export default {
  name: "DatePicker",
  props: {
    label: {
      type: String
    },
    value: {
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

            M.Datepicker.init(this.$refs.datePicker, {
                defaultTime: 'now',
                autoClose: true,
                defaultDate: this.value,
                setDefaultDate: true,
                minDate: new Date(),
                firstDay: 1,
                yearRange: 5,
                onSelect: newDate => {
                    if (newDate.getTime() === this.value.getTime()) {
                        return;
                    }

                    this.$nextTick(() => this.$emit('input', newDate));
                }
            });
        },
        beforeDestroy: function () {
            const instance = M.Datepicker.getInstance(this.$refs.datePicker);
            instance.destroy();
        },
        watch: {
            'value': {
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
    .date-picker.headless >>> .datepicker-date-display {
        display: none;
    }
</style>