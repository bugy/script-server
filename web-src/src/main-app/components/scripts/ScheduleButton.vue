<template>
    <button :class="{ 'short-view': shortView, disabled: disabled }"
            :disabled="disabled"
            @click="onClick"
            class="schedule-button btn btn-flat waves-effect"
            title="Schedule"
            v-trim-text>
        <i class="material-icons left" v-if="shortView">date_range</i>
        <span v-else>Schedule</span>
    </button>
</template>

<script>
    export default {
        name: 'ScheduleButton',
        props: {
            disabled: {
                type: Boolean,
                default: false
            },
        },
        data() {
            return {
                widthForText: 0,
                shortView: true
            }
        },
        mounted() {
            window.addEventListener('resize', this.onResize);
            this.onResize();
        },
        methods: {
            onResize() {
                this.shortView = window.innerWidth <= 400;
            },
            onClick() {
                this.$emit('click');
            }
        },
        beforeDestroy: function () {
            window.removeEventListener('resize', this.onResize);
        }
    }
</script>

<style scoped>
    .schedule-button {
        box-shadow: none;
        color: #26a69a;
        border: 1px solid #d9d9d9;
        padding-left: 16px;
        padding-right: 16px;
    }

    .schedule-button.disabled {
        color: #9F9F9F;
    }

    .schedule-button i {
        font-size: 22px;
        line-height: 34px;
        margin-right: 8px;
    }

    .schedule-button.short-view {
        padding-left: 8px;
        padding-right: 8px;
    }

    .schedule-button.short-view i {
        margin-right: 0;
    }

</style>