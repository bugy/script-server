<template>
  <div class="script-header main-content-header">
    <h2 v-show="selectedScript" class="header">{{ selectedScript }}</h2>
    <ExecutionInstanceTabs/>
  </div>
</template>

<script>
import ExecutionInstanceTabs from '@/main-app/components/scripts/ExecutionInstanceTabs';
import {mapState} from 'vuex';

export default {
  name: 'ScriptHeader',

  components: {ExecutionInstanceTabs},
  computed: {
    ...mapState('scripts', {
      selectedScript: 'selectedScript'
    }),
    ...mapState('executions', ['currentExecutor', 'executors'])
  },
  methods: {}
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

</style>