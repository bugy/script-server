<template>
  <div v-trim-text
       :class="{'margin-top': !!separator.title}"
       class="parameter-separator">
    <h6 v-if="separator.title">{{ separator.title }}</h6>
    <div v-if="separator.type === 'line'" class="separator-line"/>
  </div>
</template>

<script>
export default {
  name: 'ParameterSeparator',
  props: {
    separator: {
      type: Object
    }
  }
}
</script>

<style scoped>
.parameter-separator {
  display: flex;
  align-items: center;
  min-height: 1.3rem;
}

.margin-top {
  margin-top: 8px;
}

.parameter-separator h6 {
  margin-right: 16px;
  color: var(--primary-color);
}

.separator-line {
  height: 1px;
  border-top: 1px solid var(--separator-color);
  flex: 1 1 0;
}
</style>