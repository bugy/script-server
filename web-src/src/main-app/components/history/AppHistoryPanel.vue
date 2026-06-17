<template>
  <div class="app-history-panel">
    <ExecutionsLogPage :disableProgressIndicator="true" class="main-app-executions-log"/>
  </div>
</template>

<script>
import ExecutionsLogPage from '@/common/components/history/executions-log-page';
import {useHistoryStore} from '@/common/stores/history'
import {usePageStore} from '@/main-app/stores/page'

export default {
  name: 'AppHistoryPanel',
  components: {ExecutionsLogPage},

  computed: {
    loading() {
      return useHistoryStore().loading
    },
    detailsLoading() {
      return useHistoryStore().detailsLoading
    }
  },

  methods: {
    updateLoadingIndicator() {
      const val = this.$route.params.executionId ? this.detailsLoading : this.loading
      usePageStore().setLoading(val)
    }
  },

  watch: {
    loading: {
      immediate: true,
      handler() {
        this.updateLoadingIndicator()
      }
    },
    detailsLoading: {
      immediate: true,
      handler() {
        this.updateLoadingIndicator()
      }
    }
  }
}

</script>

<style scoped>
.app-history-panel {
  height: 100%;
  overflow-y: auto;

  background: var(--background-color);
  padding-bottom: 12px;

  display: flex;
  flex-direction: column;
}

.main-app-executions-log {
  height: 100%;
}
</style>