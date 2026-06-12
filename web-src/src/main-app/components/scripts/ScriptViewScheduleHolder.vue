<template>
  <div>
    <v-dialog v-if="mobileView" v-model="showSchedulePanel" width="auto">
      <SchedulePanel :mobile-view="true" @close="showSchedulePanel = false" @scheduled="onScheduled"/>
    </v-dialog>
    <SchedulePanel v-else-if="showSchedulePanel" @close="showSchedulePanel = false" @scheduled="onScheduled"/>
    <v-snackbar v-model="scheduledSnackbar" :timeout="3000">Scheduled #{{ scheduledId }}</v-snackbar>
  </div>
</template>

<script>
import SchedulePanel from '@/main-app/components/schedule/SchedulePanel';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig'

export default {
  name: 'ScriptViewScheduleHolder',

  components: {
    SchedulePanel
  },

  props: {
    scriptConfigComponentsHeight: {
      type: Number,
      default: 0
    },
  },

  data: function () {
    return {
      mobileView: false,
      showSchedulePanel: false,
      scheduledSnackbar: false,
      scheduledId: null
    }
  },

  mounted: function () {
    window.addEventListener('resize', this.resizeListener);
    this.resizeListener();
  },

  beforeUnmount: function () {
    window.removeEventListener('resize', this.resizeListener);
  },

  computed: {
    scriptConfig() {
      return useScriptConfigStore().scriptConfig
    }
  },

  methods: {
    open() {
      this.showSchedulePanel = true;
    },

    resizeListener: function () {
      // 400 for schedule panel
      this.mobileView = (window.innerHeight - this.scriptConfigComponentsHeight - 400) < 0;
    },

    onScheduled(id) {
      this.scheduledId = id;
      this.scheduledSnackbar = true;
    }
  },

  watch: {
    showSchedulePanel: function (newValue) {
      if (!newValue) {
        this.$emit('close');
      }
    },

    scriptConfig: function () {
      this.$nextTick(() => this.resizeListener());
      this.showSchedulePanel = false;
    },

    scriptConfigComponentsHeight: function () {
      this.$nextTick(() => this.resizeListener());
    }
  },
}
</script>

<style scoped>
div > .schedule-panel {
  margin-left: auto;
  margin-top: 12px;
  background-color: var(--background-color-level-4dp);
}

div > .schedule-panel :deep(.v-card-actions) {
  background: none;
}
</style>
