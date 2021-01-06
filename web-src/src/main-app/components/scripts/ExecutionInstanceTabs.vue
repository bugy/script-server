<template>
  <div v-if="hasExecutors" class="execution-instance-tabs">
    <ul ref="tabs" class="execution-tabs">
      <li v-for="executor in scriptExecutors" :ref="'executor' + executor.state.id" class="tab executor-tab">
        <a v-trim-text
           :class="{active: (executor === currentExecutor), finished: (executor.state.status === 'finished')}"
           class="btn-flat"
           @click="selectExecutor(executor)">
          <i class="material-icons">{{ executor.state.status === 'finished' ? 'check' : 'lens' }}</i>
          {{ executor.state.id }}
        </a>
      </li>
      <li v-if="scriptExecutors && hasMoreSpace" ref="newExecutorTab" class="tab">
        <a :class="{active: !currentExecutor}"
           class="btn-flat add-execution-tab-button"
           title="Add another script instance"
           @click="addNew">
          <i class=" material-icons">add</i>
        </a>
      </li>
    </ul>
    <div ref="tabIndicator" :class="{inactive:loading}" class="tab-indicator"></div>
  </div>
</template>

<script>
import {forEachKeyValue, isEmptyArray, isNull} from '@/common/utils/common';
import {mapActions, mapState} from 'vuex';

export default {
  name: 'ExecutionInstanceTabs',
  data() {
    return {
      hasMoreSpace: {
        type: Boolean,
        default: false
      }
    }
  },
  computed: {
    ...mapState('scripts', {
      selectedScript: 'selectedScript'
    }),
    ...mapState('scriptConfig', {
      loading: 'loading'
    }),
    ...mapState('executions', ['currentExecutor', 'executors']),

    scriptExecutors() {
      const result = [];

      forEachKeyValue(this.executors, (_, executor) => {
        if (executor.state.scriptName === this.selectedScript) {
          result.push(executor);
        }
      });

      return result;
    },

    hasExecutors() {
      return !isEmptyArray(this.scriptExecutors)
    }
  },
  mounted() {
    this.updateTabIndicator();

    window.addEventListener('resize', this.onResize);
    this.calcAvailableSpace();
  },
  methods: {
    ...mapActions('executions', ['selectExecutor']),
    ...mapActions(['resetScript']),
    addNew() {
      this.selectExecutor(null);
      this.resetScript();
    },
    onResize() {
      this.updateTabIndicator();
      this.calcAvailableSpace();
    },
    updateTabIndicator() {
      if (!this.$refs.tabs) {
        return;
      }

      let tabElement = null;

      if (isNull(this.currentExecutor)) {
        if (isNull(this.$refs.newExecutorTab)) {
          this.$refs.tabIndicator.style.width = 0;
          return;
        }

        tabElement = this.$refs.newExecutorTab;

      } else {
        const ref = 'executor' + this.currentExecutor.state.id;
        tabElement = this.$refs[ref];
        if (Array.isArray(tabElement)) {
          tabElement = tabElement[0];
        }
      }

      if (!tabElement) {
        this.$refs.tabIndicator.style.width = 0;
      } else {
        const tabButton = tabElement.getElementsByClassName('btn-flat')[0];
        this.$refs.tabIndicator.style.width = tabButton.offsetWidth + 'px';
        this.$refs.tabIndicator.style.left = tabButton.offsetLeft + 'px';
      }
    },

    calcAvailableSpace() {
      if (!this.$refs.tabs) {
        return;
      }
      const childrenWidth = Array.from(this.$refs.tabs.childNodes)
          .map(c => c.offsetWidth)
          .reduce((previousValue, currentValue) => currentValue + previousValue, 0);

      this.hasMoreSpace = (this.$el.offsetWidth - childrenWidth) > 100;
    }
  },
  watch: {
    currentExecutor: {
      immediate: true,
      handler() {
        this.$nextTick(this.updateTabIndicator);
      }
    },
    loading: {
      handler() {
        this.$nextTick(this.updateTabIndicator);
      }
    },
    scriptExecutors() {
      this.$nextTick(this.updateTabIndicator);
      this.$nextTick(this.calcAvailableSpace);
    }
  },
  beforeDestroy: function () {
    window.removeEventListener('resize', this.onResize);
  }
}


</script>

<style scoped>
.execution-instance-tabs {
  height: 100%;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.execution-instance-tabs .execution-tabs {
  display: flex;
  align-items: center;
  margin-top: 0;
  margin-bottom: 0;
  height: 100%;
}

.execution-instance-tabs .tab {
  padding: 0;
  height: 100%;
}

.execution-instance-tabs .tab .btn-flat {
  height: 100%;

  display: flex;
  align-items: center;
}

.execution-instance-tabs .executor-tab > a {
  color: var(--font-color-disabled);

  font-size: 22px;
  font-weight: 300;
  line-height: 21px;
  text-transform: none;
  vertical-align: bottom;

  padding: 0 20px 0;
  height: 100%;
}

.execution-instance-tabs .executor-tab > a > i {
  font-size: 14px;
  margin-right: 12px;
}

.execution-instance-tabs .executor-tab > a.finished > i {
  font-size: 22px;
  margin-right: 6px;
  margin-left: -2px;
}

.execution-instance-tabs .tab > a.active {
  color: var(--font-color-main);
}

.execution-instance-tabs .tab > a.active > i {
  color: var(--primary-color);
}

.execution-instance-tabs .tab-indicator {
  position: absolute;
  bottom: -1px;
  height: 4px;
  width: 88px;
  background-color: var(--primary-color);
  transition: left 0.3s;
}

.execution-instance-tabs .tab-indicator.inactive {
  background-color: var(--focus-color);
}

.add-execution-tab-button {
  padding-left: 12px;
  padding-right: 12px;
}

.add-execution-tab-button i {
  font-size: 24px;
  color: var(--font-color-medium);
}

.execution-instance-tabs a.add-execution-tab-button.active i {
  color: var(--font-color-main);
}


</style>