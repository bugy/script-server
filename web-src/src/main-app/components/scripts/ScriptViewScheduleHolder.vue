<template>
  <div>
    <div v-if="mobileView && showSchedulePanel" ref="scheduleModal" class="modal">
      <SchedulePanel :mobile-view="true" @close="showSchedulePanel = false"/>
    </div>
    <SchedulePanel v-else-if="showSchedulePanel" @close="showSchedulePanel = false"/>
  </div>
</template>

<script>
import {mapState} from "vuex";
import {isNull} from "@/common/utils/common";
import SchedulePanel from "@/main-app/components/schedule/SchedulePanel";

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
      scheduleModal: null
    }
  },

  mounted: function () {
    window.addEventListener('resize', this.resizeListener);
    this.resizeListener();
  },

  beforeDestroy: function () {
    window.removeEventListener('resize', this.resizeListener);
  },

  computed: {
    ...mapState('scriptConfig', {
      scriptConfig: 'scriptConfig'
    }),
  },

  methods: {
    open() {
      this.showSchedulePanel = true;
    },

    resizeListener: function () {
      // 400 for schedule panel
      this.mobileView = (window.innerHeight - this.scriptConfigComponentsHeight - 400) < 0;
    },

    updateScheduleVisibility: function () {
      if (!this.mobileView || !this.showSchedulePanel) {
        if (!isNull(this.scheduleModal)) {
          this.scheduleModal.destroy();
          this.scheduleModal = null;
        }
      } else {
        if (isNull(this.scheduleModal)) {
          this.scheduleModal = M.Modal.init(this.$refs.scheduleModal,
              {onCloseStart: () => this.showSchedulePanel = false});
        }
        this.scheduleModal.open();
      }
    }

  },

  watch: {
    mobileView: function () {
      this.$nextTick(() => {
        this.updateScheduleVisibility()
      });
    },

    showSchedulePanel: function (newValue) {
      this.$nextTick(() => {
        this.updateScheduleVisibility()
      });

      if (!newValue) {
        this.$emit('close');
      }
    },

    scriptConfig: function () {
      this.$nextTick(() => this.resizeListener())
      this.showSchedulePanel = false;
    },

    scriptConfigComponentsHeight: function () {
      this.$nextTick(() => this.resizeListener());
    }
  },
}

</script>

<style scoped>
.modal {
  width: fit-content;
}

.modal .schedule-panel {
  margin: 0;
}

div:not(.modal) > .schedule-panel {
  margin-left: auto;
  margin-top: 12px;
  background-color: var(--background-color-level-4dp);
}

div:not(.modal) > .schedule-panel >>> .card-action {
  background: none;
}
</style>