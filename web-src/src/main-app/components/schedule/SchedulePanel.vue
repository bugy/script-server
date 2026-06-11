<template>
  <div class="schedule-panel card">
    <div class="card-content">
      <span class="card-title primary-color-text">Schedule execution</span>
      <div class="schedule-type-panel">
        <p class="schedule-type-field">
          <label>
            <input :checked="oneTimeSchedule" class="with-gap" name="schedule-type"
                   type="radio"
                   @click="oneTimeSchedule = true"/>
            <span>One time</span>
          </label>
        </p>
        <p class="schedule-type-field">
          <label>
            <input :checked="!oneTimeSchedule" class="with-gap" name="schedule-type"
                   type="radio"
                   @click="oneTimeSchedule = false"/>
            <span>Repeat</span>
          </label>
        </p>
      </div>
      <div v-if="oneTimeSchedule" class="one-time-schedule-panel">
        <DatePicker v-model="startDate" :show-header-in-modal="!mobileView" class="inline" label="Date"/>
        <TimePicker v-model="startTime" class="inline" label="Time" @error="onFieldError('startTime', $event)"/>
      </div>
      <div v-else class="repeat-schedule-panel">
        <div>
          <span class="schedule-repeat_col-1">Every</span>
          <Textfield v-model="repeatPeriod" :config="repeatPeriodField"
                     class="inline repeat-period-field schedule-repeat_col-2" @error="onFieldError('repeatPeriod', $event)"/>
          <Combobox v-model="repeatTimeUnit" :config="repeatTimeUnitField"
                    :show-header="false" class="inline repeat-time-unit-field schedule-repeat_col-3"/>
        </div>
        <div>
          <span class="schedule-repeat_col-1">Starting</span>
          <DatePicker v-model="startDate"
                      :show-header-in-modal="!mobileView"
                      class="inline repeat-start-date schedule-repeat_col-2" label="Date"/>
          <TimePicker v-model="startTime" class="inline repeat-start-time schedule-repeat_col-3"
                      label="Time" @error="onFieldError('startTime', $event)"/>
        </div>

        <div>
          <span class="schedule-repeat_col-1">End:</span>
          <div class="schedule-type-panel">
            <p class="schedule-type-field">
              <label>
                <input :checked="endOption === 'never'" class="with-gap" name="end-type" type="radio" @click="endOption = 'never'" />
                <span>Never</span>
              </label>
            </p>
            <p class="schedule-type-field">
              <label>
                <input :checked="endOption === 'maxExecuteCount'" class="with-gap" name="end-type" type="radio" @click="endOption = 'maxExecuteCount'" />
                <span>Count</span>
              </label>
            </p>
            <p class="schedule-type-field">
              <label>
                <input :checked="endOption === 'endDatetime'" class="with-gap" name="end-type" type="radio" @click="endOption = 'endDatetime'" />
                <span>Date</span>
              </label>
            </p>
          </div>
          <br>
          <div v-if="endOption === 'endDatetime'">
            <span class="schedule-repeat_col-1">Ending</span>
            <DatePicker v-model="endDate" :show-header-in-modal="!mobileView" class="inline repeat-start-date schedule-repeat_col-2" label="Date" />
            <TimePicker v-model="endTime" class="inline repeat-start-time schedule-repeat_col-3" label="Time" @error="onFieldError('endTime', $event)" />
          </div>
          <div v-if="endOption === 'maxExecuteCount'">
            <span class="schedule-repeat_col-1">Count</span>
            <Textfield v-model="maxExecuteCount" :config="repeatPeriodField" class="inline repeat-period-field schedule-repeat_col-2" @error="onFieldError('maxExecuteCount', $event)" />
          </div>

        <div v-if="repeatTimeUnit === 'weeks'" class="repeat-weeks-panel">
          <div :class="{ error: weekdaysError }" class="repeat-weekday-panel">
            <ToggleDayButton v-for="day in weekDays"
                             :key="day.day"
                             v-model="day.active"
                             :text="day.day.charAt(0)"
                             :title="day.day"/>
          </div>
          <div v-if="weekdaysError" class="weekdays-error">{{ weekdaysError }}</div>
        </div>
      </div>
    </div>
    <div class="schedule-panel-buttons card-action">
      <a class="waves-effect btn-flat" @click="close">
        Cancel
      </a>
      <PromisableButton :click="runScheduleAction"
                        :enabled="errors.length === 0"
                        :preloaderStyle="{ width: '20px', height: '20px' }"
                        title="Schedule"/>
    </div>
    </div>
  </div>
</template>

<script>
// input-fields provides M.updateTextFields; it used to be pulled in globally
// by the Textfield component before its Vuetify migration.
import '@/common/materializecss/imports/input-fields'
import DatePicker from "@/common/components/inputs/DatePicker";
import TimePicker from "@/common/components/inputs/TimePicker";
import Textfield from "@/common/components/textfield";
import Combobox from "@/common/components/combobox";
import '@/common/materializecss/imports/cards';
import {repeatPeriodField, repeatTimeUnitField} from "@/main-app/components/schedule/schedulePanelFields";
import ToggleDayButton from "@/main-app/components/schedule/ToggleDayButton";
import PromisableButton from "@/common/components/PromisableButton";
import {mapActions} from "vuex";
import '@/common/materializecss/imports/toast'
import {clearArray, isEmptyArray, isEmptyString} from "@/common/utils/common";

export default {
  name: 'SchedulePanel',
  components: {PromisableButton, ToggleDayButton, Combobox, Textfield, TimePicker, DatePicker},
  props: {
    mobileView: {
      type: Boolean,
      default: false
    },
  },

  data() {
    const now = new Date();
    const currentDay = now.getDay();

    const endDay = new Date(now);
    endDay.setDate(now.getDate() + 1);

    return {
      oneTimeSchedule: true,
      startDate: now,
      startTime: now.toTimeString().substr(0, 5),
      endOption: 'never',
      endDate: endDay,
      endTime: endDay.toTimeString().substr(0, 5),
      id: null,
      repeatPeriod: 1,
      maxExecuteCount: 1,
      repeatTimeUnit: 'days',
      weekDays: [
        {'day': 'Monday', active: currentDay === 1},
        {'day': 'Tuesday', active: currentDay === 2},
        {'day': 'Wednesday', active: currentDay === 3},
        {'day': 'Thursday', active: currentDay === 4},
        {'day': 'Friday', active: currentDay === 5},
        {'day': 'Saturday', active: currentDay === 6},
        {'day': 'Sunday', active: currentDay === 0}
      ],

      repeatPeriodField,
      repeatTimeUnitField,
      errors: [],
      fieldErrors: {}
    }
  },
  mounted: function () {
    this.id = this.$.uid;

    M.updateTextFields();
  },

  methods: {
    ...mapActions('scriptSchedule', ['schedule']),

    runScheduleAction() {
      const scheduleSetup = this.buildScheduleSetup();
      return this.schedule({scheduleSetup})
          .then(({data: response}) => {
            M.toast({html: 'Scheduled #' + response['id']});
            this.close();
          });
    },

    buildScheduleSetup() {
      const startDatetime = new Date(this.startDate);
      const [hours, minutes] = this.startTime.split(':');
      startDatetime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

      let endOption = this.endOption;
      let endArg = null;

      if (this.endOption === 'maxExecuteCount') {
        endArg = this.maxExecuteCount;
        endOption = 'max_executions';
      } else if (this.endOption === 'endDatetime') {
        const endDatetime = new Date(this.endDate);
        const [hoursEnd, minutesEnd] = this.endTime.split(':');
        endDatetime.setHours(parseInt(hoursEnd), parseInt(minutesEnd), 0, 0);
        endArg = endDatetime;
        endOption = 'end_datetime';
      }

      const weekDays = this.weekDays.filter(day => day.active).map(day => day.day);

      return {
        repeatable: !this.oneTimeSchedule,
        startDatetime: startDatetime,
        endOption: endOption,
        endArg: endArg,
        repeatUnit: this.repeatTimeUnit,
        repeatPeriod: this.repeatPeriod,
        weekDays: weekDays
      };
    },

    close() {
      this.$emit('close');
    },

    onFieldError(fieldKey, error) {
      this.fieldErrors[fieldKey] = error;
      this.checkErrors();
    },

    checkErrors() {
      clearArray(this.errors);

      // Vue 3 fix: $children is gone; field errors arrive through the @error
      // events and are kept in fieldErrors. Only the fields rendered in the
      // current mode count (same as the old walk over mounted children).
      const activeKeys = ['startTime'];
      if (!this.oneTimeSchedule) {
        activeKeys.push('repeatPeriod');
        if (this.endOption === 'endDatetime') {
          activeKeys.push('endTime');
        }
        if (this.endOption === 'maxExecuteCount') {
          activeKeys.push('maxExecuteCount');
        }
      }

      for (const key of activeKeys) {
        if (!isEmptyString(this.fieldErrors[key])) {
          this.errors.push(this.fieldErrors[key]);
        }
      }

      if (!isEmptyString(this.weekdaysError)) {
        this.errors.push(this.weekdaysError);
      }
    }
  },

  computed: {
    weekdaysError() {
      if (this.oneTimeSchedule || this.repeatTimeUnit !== 'weeks') {
        return null;
      }

      const activeWeekDays = this.weekDays.filter(day => day.active);
      if (isEmptyArray(activeWeekDays)) {
        return 'required';
      }

      return null;
    }
  },

  watch: {
    weekdaysError() {
      this.$nextTick(this.checkErrors);
    },

    oneTimeSchedule() {
      this.$nextTick(this.checkErrors);
    },

    endOption() {
      this.$nextTick(this.checkErrors);
    }
  }

}
</script>

<style scoped>

.schedule-panel {
  font-size: 16px;
  max-width: 320px;
  width: 100%;
  height: 480px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.schedule-panel .card-title {
  font-size: 20px;
}

.schedule-panel .card-content {
  padding-top: 12px;
  padding-bottom: 12px;
}

.schedule-panel .input-field.inline {
  margin-top: 8px;
  margin-bottom: 8px;
  vertical-align: baseline;
}

.schedule-panel .input-field.inline:after {
  top: 3.9em;
  left: 0;
  font-size: 12px;
  white-space: nowrap;
}

.schedule-panel .schedule-type-field {
  display: inline;
  margin-right: 32px;
}

.schedule-panel .schedule-type-field:last-child {
  margin-right: 0;
}

.schedule-panel .with-gap + span {
  font-size: 16px;
}

.schedule-panel .with-gap:checked + span {
  color: var(--font-color-main);
}

.toggle-day-button {
  display: inline-block;
  margin-right: 8px;
}

.toggle-day-button:last-child {
  margin-right: 0;
}

.schedule-panel input[type="radio"]:not(:checked) + span:before {
  border: 2px solid var(--font-color-medium);
}

.schedule-type-panel {
  margin-top: 16px;
  margin-bottom: 0;
  margin-left: -3px;
}

.one-time-schedule-panel {
  margin-top: 24px;
}

.one-time-schedule-panel .date-picker {
  width: 50%
}

.one-time-schedule-panel .time-picker {
  width: calc(45% - 32px)
}

.one-time-schedule-panel .time-picker {
  margin-left: 32px;
}

.repeat-schedule-panel {
  margin-top: 16px;
}

.repeat-schedule-panel span {
  display: inline-block;
}

.repeat-schedule-panel .schedule-repeat_col-12 {
  width: 65%;
  margin: 0 5% 0 0;
}

.repeat-schedule-panel .schedule-repeat_col-1 {
  width: 20%;
  margin: 0;
}

.repeat-schedule-panel .schedule-repeat_col-2 {
  width: 35%;
  margin-left: 10%;
  margin-right: 5%;
}

.repeat-schedule-panel .schedule-repeat_col-3 {
  width: 30%;
  margin: 0;
}

.schedule-panel-buttons.card-action {
  display: flex;
  justify-content: flex-end;
  padding: 8px;
}

.schedule-panel .schedule-panel-buttons.card-action a.btn-flat {
  margin-right: 8px;
}

.schedule-panel .repeat-weekday-panel {
  margin-bottom: 16px;
  padding-bottom: 8px;
  width: fit-content;
  height: 36px;
  box-sizing: border-box;
}

.schedule-panel .repeat-weekday-panel.error {
  border-bottom: 1px solid #F44336;
}

.repeat-weeks-panel {
  position: relative;
}

.schedule-panel .weekdays-error {
  color: #F44336;
  position: absolute;
  font-size: 12px;
  top: 40px;
  right: 32px;
}

@media (max-width: 320px) {
  .toggle-day-button {
    margin-right: 4px;
  }
}

@media (max-height: calc(600px)) {
  .schedule-panel {
    height: 340px;
  }

  .schedule-panel .input-field.inline {
    margin-top: 0;
    margin-bottom: 0;
  }
}
</style>