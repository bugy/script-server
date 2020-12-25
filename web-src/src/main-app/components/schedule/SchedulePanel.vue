<template>
    <div class="schedule-panel card">
        <div class="card-content">
            <span class="card-title primary-color-text">Schedule execution</span>
            <div class="schedule-type-panel">
                <p class="schedule-type-field">
                    <label>
                        <input :checked="oneTimeSchedule" @click="oneTimeSchedule = true" class="with-gap"
                               name="schedule-type"
                               type="radio"/>
                        <span>One time</span>
                    </label>
                </p>
                <p class="schedule-type-field">
                    <label>
                        <input :checked="!oneTimeSchedule" @click="oneTimeSchedule = false" class="with-gap"
                               name="schedule-type"
                               type="radio"/>
                        <span>Repeat</span>
                    </label>
                </p>
            </div>
            <div class="one-time-schedule-panel" v-if="oneTimeSchedule">
                <DatePicker :show-header-in-modal="!mobileView" class="inline" label="Date" v-model="startDate"/>
                <TimePicker @error="checkErrors" class="inline" label="Time" v-model="startTime"/>
            </div>
            <div class="repeat-schedule-panel" v-else>
                <div>
                    <span class="schedule-repeat_col-1">Every</span>
                    <Textfield :config="repeatPeriodField" @error="checkErrors"
                               class="inline repeat-period-field schedule-repeat_col-2" v-model="repeatPeriod"/>
                    <Combobox :config="repeatTimeUnitField" :show-header="false"
                              class="inline repeat-time-unit-field schedule-repeat_col-3" v-model="repeatTimeUnit"/>
                </div>
                <div>
                    <span class="schedule-repeat_col-1">Starting</span>
                    <DatePicker :show-header-in-modal="!mobileView"
                                class="inline repeat-start-date schedule-repeat_col-2"
                                label="Date" v-model="startDate"/>
                    <TimePicker @error="checkErrors" class="inline repeat-start-time schedule-repeat_col-3"
                                label="Time" v-model="startTime"/>
                </div>

                <div class="repeat-weeks-panel" v-if="repeatTimeUnit === 'weeks'">
                    <div :class="{ error: weekdaysError }" class="repeat-weekday-panel">
                        <ToggleDayButton :key="day.day"
                                         :text="day.day.charAt(0)"
                                         :title="day.day"
                                         v-for="day in weekDays"
                                         v-model="day.active"/>
                    </div>
                    <div class="weekdays-error" v-if="weekdaysError">{{weekdaysError}}</div>
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
</template>

<script>
import '@/common/materializecss/imports/datepicker'
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

    return {
      oneTimeSchedule: true,
      startDate: now,
      startTime: now.toTimeString().substr(0, 5),
      id: null,
      repeatPeriod: 1,
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
                errors: []
            }
        },
        mounted: function () {
            this.id = this._uid;

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
                const [hours, minutes] = this.startTime.split(':')
                startDatetime.setHours(parseInt(hours), parseInt(minutes), 0, 0)

                const weekDays = this.weekDays.filter(day => day.active)
                    .map(day => day.day);

                return {
                    repeatable: !this.oneTimeSchedule,
                    startDatetime: startDatetime,
                    repeatUnit: this.repeatTimeUnit,
                    repeatPeriod: this.repeatPeriod,
                    weekDays: weekDays
                };
            },

            close() {
                this.$emit('close');
            },

            checkErrors() {
                clearArray(this.errors);

                for (const child of this.$children) {
                    if ((child.$options._componentTag === TimePicker.name)
                        || (child.$options._componentTag === Textfield.name)) {
                        if (!isEmptyString(child.error)) {
                            this.errors.push(child.error);
                        }
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
            }
        }

    }
</script>

<style scoped>

    .schedule-panel {
        font-size: 16px;
        max-width: 320px;
        width: 100%;
        height: 380px;
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