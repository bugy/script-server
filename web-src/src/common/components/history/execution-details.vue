<template>
  <div class="execution-details container">
    <div>
      <readonly-field :value="script" class="readonly-field" title="Script name"/>
      <readonly-field :value="user" class="readonly-field" title="User"/>
      <readonly-field :value="startTime" class="readonly-field" title="Start time"/>
      <readonly-field :value="fullStatus" class="readonly-field" title="Status"/>
      <readonly-field :value="command" class="long readonly-field" title="Command"/>
    </div>
    <log-panel ref="logPanel" :autoscrollEnabled="false" class="log-panel"/>
  </div>
</template>

<script>
import {isNull} from '@/common/utils/common';
import {mapActions, mapState} from 'vuex';
import LogPanel from '../log_panel';
import ReadOnlyField from '../readonly-field';

export default {
  name: 'execution-details',

  props: {
    executionId: String
  },

  data: function () {
    return {
      script: '',
      user: '',
      startTime: '',
      fullStatus: '',
      command: '',
      mounted: false
    };
  },

  components: {
    'readonly-field': ReadOnlyField,
    'log-panel': LogPanel
  },

  methods: {
    ...mapActions('history', ['selectExecution']),

    setLog(log) {
      if (!this.mounted) {
        return;
      }

      if (!this.$refs.logPanel) {
        this.$nextTick(() => {
          this.$refs.logPanel.setLog(log);
        });
      } else {
        this.$refs.logPanel.setLog(log);
      }
    },

    refreshData(selectedExecution) {
      if (!isNull(selectedExecution)) {
        this.script = selectedExecution.script;
        this.user = selectedExecution.user;
        this.startTime = selectedExecution.startTimeString;
        this.fullStatus = selectedExecution.fullStatus;
        this.command = selectedExecution.command;
        this.setLog(selectedExecution.log);

      } else {
        this.script = '';
        this.user = '';
        this.startTime = '';
        this.fullStatus = '';
        this.command = '';
        this.setLog('');
      }
    }
  },

  computed: {
    ...mapState('history', ['selectedExecution'])
  },

  mounted() {
    this.mounted = true;
    this.refreshData(this.selectedExecution);
  },

  watch: {
    'executionId': {
      immediate: true,
      handler(executionId) {
        this.selectExecution(executionId);
      }
    },
    'selectedExecution': {
      immediate: true,
      handler(selectedExecution) {
        this.refreshData(selectedExecution);
      }
    }
  }
}
</script>

<style scoped>
.execution-details {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.readonly-field {
  margin-top: 6px;
  margin-bottom: 16px;

  display: inline-block;
  width: 200px;
}

.readonly-field.long {
  width: 600px;
  max-width: 100%;
}

.log-panel {
  margin-top: 4px;
}
</style>