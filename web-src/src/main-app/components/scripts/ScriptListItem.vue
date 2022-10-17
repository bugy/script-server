<template>
  <router-link :to="'/' + descriptor.hash"
               class="collection-item waves-effect script-list-item"
               v-bind:class="{ active: descriptor.active, 'parsing-failed': descriptor.parsingFailed}">
    {{ descriptor.name }}

    <div :class="descriptor.state" class="menu-item-state">
      <i class="material-icons check-icon">check</i>
      <div class="preloader-wrapper active">
        <div class="spinner-layer">
          <div class="circle-clipper left">
            <div class="circle"></div>
          </div>
          <div class="gap-patch">
            <div class="circle"></div>
          </div>
          <div class="circle-clipper right">
            <div class="circle"></div>
          </div>
        </div>
      </div>
    </div>
  </router-link>

</template>

<script>
import '@/common/materializecss/imports/spinner'
import {forEachKeyValue} from '@/common/utils/common';
import {mapState} from 'vuex';
import {scriptNameToHash} from '../../utils/model_helper';

export default {
  name: 'ScriptListItem',
  props: {
    script: {
      type: Object,
      default: null
    }
  },
  computed: {
    descriptor() {
      return {
        name: this.script.name,
        state: this.getState(this.script.name),
        active: this.selectedScript === this.script.name,
        hash: this.toHash(this.script.name),
        parsingFailed: this.script.parsing_failed,
      }
    },
    ...mapState('scripts', ['selectedScript'])
  },
  methods: {
    getState(scriptName) {
      let state = 'idle';

      forEachKeyValue(this.$store.state.executions.executors, function (id, executor) {
        if (executor.state.scriptName !== scriptName) {
          return;
        }

        state = executor.state.status;
      });

      return state;
    },
    toHash: scriptNameToHash
  }
}
</script>

<style scoped>
.scripts-list .collection-item {
  border: none;
  padding-right: 32px;
}

.scripts-list .collection-item.parsing-failed {
  color: var(--error-color);
}

.scripts-list .collection-item .menu-item-state {
  width: 24px;
  height: 24px;
  position: absolute;
  right: 16px;
  top: calc(50% - 12px);
  display: none;
}

.scripts-list .collection-item .menu-item-state > .check-icon {
  color: var(--primary-color);
  display: none;
  font-size: 24px;
}

.scripts-list .collection-item .menu-item-state > .preloader-wrapper {
  display: none;
  width: 100%;
  height: 100%;
}

.scripts-list .collection-item .menu-item-state.executing,
.scripts-list .collection-item .menu-item-state.finished {
  display: inline;
}

.scripts-list .collection-item .menu-item-state.executing > .check-icon {
  display: none;
}

.scripts-list .collection-item .menu-item-state.executing > .preloader-wrapper {
  display: block;
}

.scripts-list .collection-item .menu-item-state.finished > .check-icon {
  display: block;
}

.scripts-list .collection-item .menu-item-state.finished > .preloader-wrapper {
  display: none;
}

.scripts-list .collection-item .preloader-wrapper .spinner-layer {
  border-color: var(--primary-color);
}
</style>