<template>
  <div class="script-header main-content-header">
    <h2 v-show="selectedScript" class="header">{{ selectedScript }}</h2>
    <ExecutionInstanceTabs/>
    <div class="spacer"></div>
    <v-btn
      icon="history"
      variant="text"
      density="compact"
      class="button-history"
      title="Parameter History"
      @click="openParameterHistory"
    />
    <ParameterHistoryModal ref="parameterHistoryModal" :scriptName="selectedScript" @use-parameters="handleUseParameters"/>
  </div>
</template>

<script>
import ExecutionInstanceTabs from '@/main-app/components/scripts/ExecutionInstanceTabs';
import ParameterHistoryModal from '@/main-app/components/scripts/ParameterHistoryModal';
import {useScriptsStore} from '@/main-app/stores/scripts'
import {useScriptSetupStore} from '@/main-app/stores/scriptSetup'

export default {
  name: 'ScriptHeader',

  components: {ExecutionInstanceTabs, ParameterHistoryModal},
  computed: {
    selectedScript() {
      return useScriptsStore().selectedScript
    }
  },
  methods: {
    openParameterHistory() {
      this.$refs.parameterHistoryModal.open();
    },

    handleUseParameters(values) {
      for (const [parameterName, value] of Object.entries(values)) {
        useScriptSetupStore().setParameterValue({parameterName, value})
      }
    }
  }
}
</script>

<style scoped>
.script-header {
  display: flex;
  align-items: center;
  height: 56px;
}

.script-header h2.header {
  padding: 0;
  margin-right: 24px;
  flex: 0 0 auto;

  line-height: 1.7em;
  font-size: 1.7em;
}

.execution-instance-tabs {
  flex: 1 1 0;
  min-width: 0;
}

.spacer {
  flex: 1 1 0;
}

.button-history {
  margin-right: 16px;
  color: var(--font-color-medium);
}
</style>