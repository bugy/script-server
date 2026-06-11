<template>
  <v-radio-group
      :class="{horizontal}"
      :inline="horizontal"
      :model-value="modelValue"
      class="radio-group"
      density="compact"
      hide-details
      @update:model-value="$emit('update:modelValue', $event)">
    <v-radio
        v-for="option in options"
        :key="option.value"
        :class="{active: option.value === modelValue}"
        :name="groupName"
        :value="option.value"
        color="primary">
      <template #label>
        <span>{{ option.text }}</span>
        <i v-if="option.icon" :title="option.iconTitle" class="material-icons option-icon">{{ option.icon }}</i>
      </template>
    </v-radio>
  </v-radio-group>
</template>

<script>
// Vuetify migration: v-radio-group/v-radio replace the materialize radio
// markup. Also moved to the Vue 3 v-model contract (modelValue /
// update:modelValue) — the old value/input pair silently broke v-model
// bindings under Vue 3.
export default {
  name: 'RadioGroup',
  emits: ['update:modelValue'],
  props: {
    modelValue: String,
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
.radio-group.horizontal :deep(.v-radio:not(:last-child)) {
  margin-right: 32px;
}

.radio-group :deep(.v-radio) {
  position: relative;
}

.radio-group i.option-icon {
  position: absolute;
  right: -20px;
  font-size: 16px;
  color: var(--font-color-medium);
}

.radio-group .active i.option-icon {
  color: var(--font-color-main);
}

</style>
