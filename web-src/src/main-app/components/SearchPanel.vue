<template>
  <div class="search-panel-root">
    <div :class="{collapsed: !showSearchField}" class="search-panel">
      <v-text-field
        v-show="showSearchField"
        ref="searchField"
        :model-value="modelValue"
        @update:model-value="$emit('update:modelValue', $event)"
        @blur="focusLostHandler"
        density="compact"
        variant="plain"
        placeholder="Search script"
        hide-details
        autocomplete="off"
        class="search-field"
      />
    </div>
    <v-btn
      :icon="showSearchField ? 'close' : 'search'"
      variant="text"
      color="primary"
      density="compact"
      @click="clickHandler"
      @mousedown.prevent
    />
  </div>
</template>

<script>
export default {
  name: 'SearchPanel',
  emits: ['update:modelValue'],
  data() {
    return {
      showSearchField: false
    }
  },
  props: {
    modelValue: {
      type: String,
      default: ''
    }
  },
  methods: {
    clickHandler() {
      if (this.showSearchField) {
        this.showSearchField = false;
        this.$emit('update:modelValue', '');
      } else {
        this.showSearchField = true;
        this.$nextTick(() => {
          this.$refs.searchField.focus();
        });
      }
    },
    focusLostHandler() {
      if (this.modelValue === '') {
        this.showSearchField = false;
      }
    }
  }
}
</script>

<style scoped>
.search-panel-root {
  display: flex;
  align-items: center;
}

.search-panel {
  width: calc(100% - 80px - 10px);
  position: absolute;
  top: 0;
  right: 80px;
  background: var(--background-color);
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.search-panel.collapsed {
  width: 0;
}

.search-field {
  width: 100%;
  padding: 0 10px;
}
</style>
