<template>
  <div class="container">
    <PageProgress v-if="loading && !disableProgressIndicator"/>
    <div v-else class="history-log-content">
      <executions-log-table :rowClick="goToLog" :rows="executionRows"/>
      <Paginator
        :page="page"
        :pageSize="pageSize"
        :total="total"
        :totalPages="totalPages"
        :pageSizeOptions="pageSizeOptions"
        :disabled="loading"
        @page-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>
  </div>
</template>

<script>
import {mapActions, mapState} from 'vuex';
import PageProgress from '../PageProgress';
import ExecutionsLogTable from './executions-log-table';
import Paginator from './Paginator';

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
    PageProgress,
    Paginator
  },

  mounted: function () {
    this.init();
  },

  methods: {
    ...mapActions('history', ['init', 'changePage', 'changePageSize']),

    goToLog(execution_entry) {
      this.$router.push({
        path: this.$router.history.current.path + '/' + execution_entry.id
      });
    },

    onPageChange(newPage) {
      this.changePage(newPage);
    },

    onSizeChange(newSize) {
      this.changePageSize(newSize);
    }
  },

  computed: {
    ...mapState('history', {
      executionRows: 'executions',
      loading: 'loading',
      page: 'page',
      pageSize: 'pageSize',
      total: 'total',
      totalPages: 'totalPages',
      pageSizeOptions: 'pageSizeOptions'
    })
  }
}
</script>

<style scoped>
div.executions-log {
  height: 100%;
}

.history-log-content {
  display: flex;
  flex-direction: column;
}

div.progress {
  top: 45%;
}

div.indeterminate {
  max-width: 480px;
}
</style>