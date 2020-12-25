<template>
  <div v-trim-text
       :class="{active: value}"
       class="toggle-day-button"
       @click="$emit('input', !value)">
    {{ text }}
  </div>
</template>

<script>
export default {
  name: 'RoundToggleButton',
  props: {
    text: {
      type: String,
      default: '?'
    },
    value: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.toggle-day-button {
  height: 28px;
  width: 28px;
  line-height: 28px;

  text-align: center;

  border-radius: 14px;
  background-color: var(--background-color-high-emphasis);

  cursor: pointer;
  text-transform: uppercase;

  font-size: 11px;
  font-weight: 500;
  color: var(--font-color-disabled);
}

.toggle-day-button.active {
  color: var(--font-on-primary-color-main);
  background-color: var(--primary-color);
}
</style>