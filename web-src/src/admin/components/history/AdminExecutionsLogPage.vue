<template>
  <ExecutionsLogPage/>
</template>

<script>
import ExecutionsLogPage from '@/common/components/history/executions-log-page';
import {useHistoryStore} from '@/common/stores/history';
import {useAdminUiStore} from '@/admin/stores/ui';

export default {
  name: 'AdminExecutionsLogPage',
  components: {ExecutionsLogPage},

  computed: {
    selectedExecution() {
      return useHistoryStore().selectedExecution
    }
  },

  watch: {
    selectedExecution: {
      immediate: true,
      handler(execution) {
        const subheader = execution
            ? '#' + execution.id + ' - ' + execution.user + '@' + execution.script
            : null
        useAdminUiStore().setSubheader(subheader)
      }
    }
  }
}
</script>

<style scoped>

</style>