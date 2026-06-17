<template>
  <div class="container">
    <PageProgress v-if="loading && !disableProgressIndicator"/>
    <executions-log-table v-else :rowClick="goToLog" :rows="executionRows"/>
  </div>
</template>

<script>
import PageProgress from '../PageProgress';
import ExecutionsLogTable from './executions-log-table'
import {useHistoryStore} from '@/common/stores/history'

export default {
  name: 'executions-log',

  props: {
    disableProgressIndicator: {
      type: Boolean,
      default: false
    }
  },
  components: {
    'executions-log-table': ExecutionsLogTable,
    PageProgress
  },

  mounted() {
    useHistoryStore().init()
  },

  methods: {
    goToLog(execution_entry) {
      this.$router.push({path: this.$route.path + '/' + execution_entry.id})
    }
  },

  computed: {
    executionRows() {
      return useHistoryStore().executions
    },
    loading() {
      return useHistoryStore().loading
    }
  }
}


</script>

<style scoped>
div.executions-log {
  height: 100%;
}

div.progress {
  top: 45%;
}

div.indeterminate {
  max-width: 480px;
}
</style>