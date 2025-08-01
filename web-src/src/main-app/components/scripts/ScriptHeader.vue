<template>
  <div class="script-header main-content-header">
    <h2 v-show="selectedScript" class="header">{{ selectedScript }}</h2>
    <ExecutionInstanceTabs/>
    <div class="spacer"></div>
    <button class="button-history btn btn-flat"
            @click="openParameterHistory"
            title="Parameter History">
      <i class="material-icons">history</i>
    </button>
    <ParameterHistoryModal ref="parameterHistoryModal" :scriptName="selectedScript" @use-parameters="handleUseParameters"/>
  </div>
</template>

<script>
import ExecutionInstanceTabs from '@/main-app/components/scripts/ExecutionInstanceTabs';
import ParameterHistoryModal from '@/main-app/components/scripts/ParameterHistoryModal';
import {mapState} from 'vuex';

export default {
  name: 'ScriptHeader',

  components: {ExecutionInstanceTabs, ParameterHistoryModal},
  computed: {
    ...mapState('scripts', {
      selectedScript: 'selectedScript'
    }),
    ...mapState('executions', ['currentExecutor', 'executors'])
  },
  methods: {
    openParameterHistory() {
      this.$refs.parameterHistoryModal.open();
    },

    handleUseParameters(values) {
      // Set all parameter values using the scriptSetup store
      for (const [parameterName, value] of Object.entries(values)) {
        this.$store.dispatch('scriptSetup/setParameterValue', { parameterName, value });
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
  flex: 0 0 auto;
  color: var(--primary-color);
  border: 1px solid var(--outline-color);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  min-width: 40px;
}

.button-history i {
  font-size: 18px;
}
</style>