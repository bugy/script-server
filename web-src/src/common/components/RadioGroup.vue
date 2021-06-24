<template>
  <div :class="{horizontal}" class="radio-group">
    <p v-for="option in options" :class="{active: option.value === value}">
      <label>
        <input :checked="option.value === value" :name="groupName" class="with-gap"
               type="radio"
               @click="$emit('input', option.value)"/>
        <span>{{ option.text }}</span>
      </label>
      <i v-if="option.icon" :title="option.iconTitle" class="material-icons">{{ option.icon }}</i>
    </p>
  </div>
</template>

<script>
import '@/assets/css/materializecss/material-radiobuttons.css'

export default {
  name: 'RadioGroup',
  props: {
    value: String,
    groupName: String,
    horizontal: {
      type: Boolean,
      default: false
    },
    options: {
      type: Array
    }
  }

}
</script>

<style scoped>
.radio-group {
  display: flex;
  flex-direction: column;
}

.radio-group.horizontal {
  flex-direction: row;
}

.radio-group.horizontal > p:not(:last-child) {
  margin-right: 32px;
}

.radio-group p {
  position: relative;
}

.radio-group i {
  position: absolute;
  right: -20px;
  font-size: 16px;
  color: var(--font-color-medium);
}

.radio-group .active i {
  color: var(--font-color-main);
}


</style>