<template>
  <v-list-item
    :to="'/' + descriptor.hash"
    :title="descriptor.name"
    :class="{ 'parsing-failed': descriptor.parsingFailed }"
    class="script-list-item"
  >
    <v-tooltip v-if="descriptor.parsingFailed" activator="parent" location="right">
      Failed to parse config file
    </v-tooltip>
    <template #append>
      <v-progress-circular
        v-if="descriptor.state === 'executing'"
        :size="20"
        :width="2"
        color="primary"
        indeterminate
      />
      <v-icon v-else-if="descriptor.state === 'finished'" color="primary" :size="20">check</v-icon>
      <v-icon v-else-if="descriptor.state === 'cannot-parse'" color="error" :size="20">priority_high</v-icon>
    </template>
  </v-list-item>
</template>

<script>
import {forEachKeyValue} from '@/common/utils/common';
import {useScriptsStore} from '@/main-app/stores/scripts'
import {useExecutionsStore} from '@/main-app/stores/executions'
import {scriptNameToHash} from '../../utils/model_helper';

export default {
  name: 'ScriptListItem',
  props: {
    script: {
      type: Object,
      default: null
    }
  },
  computed: {
    descriptor() {
      return {
        name: this.script.name,
        state: this.getState(this.script.name),
        hash: this.toHash(this.script.name),
        parsingFailed: this.script.parsing_failed
      }
    },
    selectedScript() {
      return useScriptsStore().selectedScript
    }
  },
  methods: {
    getState(scriptName) {
      if (this.script.parsing_failed) {
        return 'cannot-parse'
      }

      let state = 'idle';
      forEachKeyValue(useExecutionsStore().executors, function (id, executor) {
        if (executor.state.scriptName !== scriptName) {
          return;
        }
        state = executor.state.status;
      });
      return state;
    },
    toHash: scriptNameToHash
  }
}
</script>

<style scoped>
.script-list-item.parsing-failed :deep(.v-list-item-title) {
  color: var(--font-color-disabled);
}
</style>
