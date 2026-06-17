<template>
  <v-tabs
    v-if="hasExecutors"
    :model-value="currentExecutor"
    :color="loading ? 'grey-lighten-1' : 'primary'"
    class="execution-instance-tabs"
    density="compact"
    @update:model-value="selectExecutor"
  >
    <v-tab
      v-for="executor in scriptExecutors"
      :key="executor.state.id"
      :value="executor"
      :class="{
        'status-finished': executor.state.status === 'finished',
        'status-error': (executor.state.status === 'error') || (executor.state.status === 'disconnected')
      }"
    >
      <v-icon class="tab-icon">{{ getExecutorIcon(executor) }}</v-icon>
      {{ executor.state.id }}
    </v-tab>
    <v-tab
      :value="null"
      class="add-execution-tab"
      title="Add another script instance"
      @click="resetScript"
    >
      <v-icon>add</v-icon>
    </v-tab>
  </v-tabs>
</template>

<script>
import {forEachKeyValue, isEmptyArray} from '@/common/utils/common';
import {useScriptsStore} from '@/main-app/stores/scripts'
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig'
import {useExecutionsStore} from '@/main-app/stores/executions'
import {useScriptSetupStore} from '@/main-app/stores/scriptSetup'

export default {
  name: 'ExecutionInstanceTabs',
  computed: {
    selectedScript() {
      return useScriptsStore().selectedScript
    },
    loading() {
      return useScriptConfigStore().loading
    },
    currentExecutor() {
      return useExecutionsStore().currentExecutor
    },
    executors() {
      return useExecutionsStore().executors
    },

    scriptExecutors() {
      const result = [];
      forEachKeyValue(this.executors, (_, executor) => {
        if (executor.state.scriptName === this.selectedScript) {
          result.push(executor);
        }
      });
      return result;
    },

    hasExecutors() {
      return !isEmptyArray(this.scriptExecutors);
    }
  },
  methods: {
    selectExecutor(executor) {
      useExecutionsStore().selectExecutor(executor)
    },
    resetScript() {
      const selectedScript = useScriptsStore().selectedScript
      useScriptSetupStore().reset()
      useScriptConfigStore().reloadScript(selectedScript)
    },

    getExecutorIcon(executor) {
      const status = executor.state.status;
      if (status === 'finished') return 'check';
      if ((status === 'error') || (status === 'disconnected')) return 'error_outline';
      return 'lens';
    }
  }
}
</script>

<style scoped>
:deep(.v-tab) {
  color: var(--font-color-disabled);
  font-size: 22px;
  font-weight: 300;
  text-transform: none;
  padding: 0 20px;
}

:deep(.v-tab--selected) {
  color: var(--font-color-main);
}

:deep(.v-tab .tab-icon) {
  font-size: 14px;
  margin-right: 12px;
}

:deep(.v-tab.status-finished .tab-icon) {
  font-size: 22px;
  margin-right: 6px;
  margin-left: -2px;
}

:deep(.v-tab.status-error .tab-icon) {
  font-size: 16px;
  margin-right: 10px;
}

:deep(.v-tab--selected .tab-icon) {
  color: var(--primary-color);
}

:deep(.add-execution-tab) {
  padding: 0 12px;
}

:deep(.add-execution-tab .v-icon) {
  font-size: 24px;
  color: var(--font-color-medium);
}

:deep(.v-tab--selected.add-execution-tab .v-icon) {
  color: var(--font-color-main);
}
</style>
