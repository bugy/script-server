<template>
  <v-btn variant="outlined"
         color="primary"
         :disabled="disabled"
         class="schedule-button"
         title="Schedule"
         @click="onClick">
    <v-icon v-if="shortView">date_range</v-icon>
    <span v-else>Schedule</span>
  </v-btn>
</template>

<script>
export default {
  name: 'ScheduleButton',
  emits: ['click'],
  props: {
    disabled: {
      type: Boolean,
      default: false
    },
  },
  data() {
    return {
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
  beforeUnmount: function () {
    window.removeEventListener('resize', this.onResize);
  }
}
</script>

<style scoped>
.schedule-button {
  box-shadow: none;
}
</style>
