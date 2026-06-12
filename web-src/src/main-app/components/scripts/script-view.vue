<template>
  <div :id="id" class="script-view">
    <ScriptLoadingText v-if="loading && !scriptConfig" :loading="loading" :script="selectedScript"/>
    <p v-show="scriptDescription" class="script-description" v-html="formattedDescription"/>
    <ScriptParametersView ref="parametersView"/>
    <div class="actions-panel">
      <v-btn color="primary"
             :disabled="!enableExecuteButton || scheduleMode"
             class="button-execute"
             @click="executeScript">
        Execute
      </v-btn>
      <v-btn :disabled="!enableStopButton"
             :color="killEnabled ? 'red-darken-3' : 'red-lighten-1'"
             class="button-stop"
             @click="stopScript">
        {{ stopButtonLabel }}
      </v-btn>
      <div v-if="schedulable" class="button-gap"></div>
      <ScheduleButton v-if="schedulable" :disabled="!enableScheduleButton" @click="openSchedule"/>
    </div>
    <LogPanel v-show="showLog && !hasErrors && !hideExecutionControls" ref="logPanel" :outputFormat="outputFormat"/>
    <LogPanel v-if="preloadOutput && !showLog && !hasErrors && !hideExecutionControls"
              ref="preloadOutputPanel"
              :output-format="preloadOutputFormat"/>
    <div v-if="hasErrors" v-show="!hideExecutionControls" class="validation-panel">
      <h6 class="header">Validation failed. Errors list:</h6>
      <ul class="validation-errors-list">
        <li v-for="error in shownErrors">{{ error }}</li>
      </ul>
    </div>
    <div v-if="downloadableFiles && (downloadableFiles.length > 0) && !scheduleMode" v-show="!hideExecutionControls"
         class="files-download-panel">
      <v-btn v-for="file in downloadableFiles"
             :key="file.filename"
             :href="file.url"
             :download="file.filename"
             variant="text"
             color="primary"
             append-icon="file_download"
             target="_blank">
        {{ file.filename }}
      </v-btn>
    </div>
    <div v-if="inputPromptText" v-show="!hideExecutionControls" class="script-input-panel">
      <v-text-field ref="inputField"
                    v-model="userInput"
                    :label="inputPromptText"
                    density="compact"
                    variant="underlined"
                    hide-details
                    @keyup.enter="onInputEnter"/>
    </div>
    <ScriptViewScheduleHolder v-if="!hideExecutionControls"
                              ref="scheduleHolder"
                              :scriptConfigComponentsHeight="scriptConfigComponentsHeight"
                              @close="scheduleMode = false"/>
  </div>
</template>

<script>

import LogPanel from '@/common/components/log_panel'
import {deepCloneObject, forEachKeyValue, isEmptyObject, isEmptyString, isNull} from '@/common/utils/common';
import ScheduleButton from '@/main-app/components/scripts/ScheduleButton';
import ScriptLoadingText from '@/main-app/components/scripts/ScriptLoadingText';
import ScriptViewScheduleHolder from '@/main-app/components/scripts/ScriptViewScheduleHolder';
import DOMPurify from 'dompurify';
import {marked} from 'marked';
import {mapActions, mapState} from 'vuex'
import {STATUS_DISCONNECTED, STATUS_ERROR, STATUS_EXECUTING, STATUS_FINISHED} from '../../store/scriptExecutor';
import ScriptParametersView from './script-parameters-view'

export default {
  data: function () {
    return {
      id: null,
      everStarted: false,
      shownErrors: [],
      nextLogIndex: 0,
      lastInlineImages: {},
      scheduleMode: false,
      scriptConfigComponentsHeight: 0,
      userInput: ''
    }
  },

  props: {
    hideExecutionControls: Boolean
  },

  mounted: function () {
    this.id = 'script-panel-' + this.$.uid;
  },

  components: {
    ScriptLoadingText,
    LogPanel,
    ScriptParametersView,
    ScheduleButton,
    ScriptViewScheduleHolder
  },

  computed: {
    ...mapState('scriptConfig', {
      scriptDescription: state => state.scriptConfig ? state.scriptConfig.description : '',
      loading: 'loading',
      scriptConfig: 'scriptConfig',
      outputFormat: state => state.scriptConfig ? state.scriptConfig.outputFormat : undefined,
      preloadOutput: state => state.preloadScript?.['output'],
      preloadOutputFormat: state => state.preloadScript?.['format']
    }),
    ...mapState('scriptSetup', {
      parameterErrors: 'errors'
    }),
    ...mapState('executions', {
      currentExecutor: 'currentExecutor'
    }),
    ...mapState('scripts', ['selectedScript']),

    hasErrors: function () {
      return !isNull(this.shownErrors) && (this.shownErrors.length > 0);
    },

    formattedDescription: function () {
      if (isEmptyString(this.scriptDescription)) {
        return '';
      }

      const descriptionHtml = DOMPurify.sanitize(marked.parse(this.scriptDescription, {gfm: true, breaks: true}));
      const paragraphRemoval = document.createElement('div');
      paragraphRemoval.innerHTML = descriptionHtml.trim();

      for (var i = 0; i < paragraphRemoval.childNodes.length; i++) {
        var child = paragraphRemoval.childNodes[i];
        if (child.tagName === 'P') {
          i += child.childNodes.length - 1;

          while (child.childNodes.length > 0) {
            paragraphRemoval.insertBefore(child.firstChild, child);
          }

          paragraphRemoval.removeChild(child);
        }
      }

      return paragraphRemoval.innerHTML;
    },

    enableExecuteButton() {
      if (this.scheduleMode) {
        return false;
      }

      if (this.hideExecutionControls) {
        return false;
      }

      if (this.loading) {
        return false;
      }

      if (isNull(this.currentExecutor)) {
        return true;
      }

      return this.currentExecutor.state.status === STATUS_FINISHED
          || this.currentExecutor.state.status === STATUS_DISCONNECTED
          || this.currentExecutor.state.status === STATUS_ERROR;
    },

    enableScheduleButton() {
      if (this.hideExecutionControls) {
        return false;
      }

      if (this.loading) {
        return false;
      }

      if (isNull(this.currentExecutor)) {
        return true;
      }

      return this.currentExecutor.state.status === STATUS_FINISHED
          || this.currentExecutor.state.status === STATUS_DISCONNECTED
          || this.currentExecutor.state.status === STATUS_ERROR;
    },

    enableStopButton() {
      return this.status === STATUS_EXECUTING;
    },

    stopButtonLabel() {
      if (this.status === STATUS_EXECUTING) {
        if (this.killEnabled) {
          return 'Kill';
        }

        if (!isNull(this.killEnabledTimeout)) {
          return 'Stop (' + this.killEnabledTimeout + ')';
        }
      }

      return 'Stop';
    },

    status() {
      return isNull(this.currentExecutor) ? null : this.currentExecutor.state.status;
    },

    showLog() {
      return !isNull(this.currentExecutor) && !this.scheduleMode;
    },

    downloadableFiles() {
      if (!this.currentExecutor) {
        return [];
      }

      return this.currentExecutor.state.downloadableFiles;
    },

    inlineImages() {
      if (!this.currentExecutor) {
        return {};
      }

      return this.currentExecutor.state.inlineImages;
    },

    inputPromptText() {
      if (this.status !== STATUS_EXECUTING) {
        return null;
      }

      return this.currentExecutor.state.inputPromptText;
    },

    logChunks() {
      if (!this.currentExecutor) {
        return [];
      }

      return this.currentExecutor.state.logChunks;
    },

    killEnabled() {
      return !isNull(this.currentExecutor) && this.currentExecutor.state.killEnabled;
    },

    killEnabledTimeout() {
      return isNull(this.currentExecutor) ? null : this.currentExecutor.state.killTimeoutSec;
    },

    schedulable() {
      return this.scriptConfig && this.scriptConfig.schedulable;
    }
  },

  methods: {
    onInputEnter: function () {
      this.sendUserInput(this.userInput);
      this.userInput = '';
    },

    validatePreExecution: function () {
      this.shownErrors = [];

      const errors = this.parameterErrors;
      if (!isEmptyObject(errors)) {
        forEachKeyValue(errors, (paramName, error) => {
          this.shownErrors.push(paramName + ': ' + error);
        });
        return false;
      }

      return true;
    },

    executeScript: function () {
      if (!this.validatePreExecution()) {
        return;
      }

      this.startExecution();
    },

    openSchedule: function () {
      if (!this.validatePreExecution()) {
        return;
      }

      this.$refs.scheduleHolder.open();
      this.scheduleMode = true;
    },

    ...mapActions('executions', {
      startExecution: 'startExecution'
    }),

    stopScript() {
      if (isNull(this.currentExecutor)) {
        return;
      }

      if (this.killEnabled) {
        this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/killExecution');
      } else {
        this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/stopExecution');
      }
    },

    sendUserInput(value) {
      if (isNull(this.currentExecutor)) {
        return;
      }

      this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/sendUserInput', value);
    },

    setLog: function (text) {
      this.$refs.logPanel.setLog(text);
    },

    appendLog: function (text) {
      this.$refs.logPanel.appendLog(text);
    },


  },

  watch: {
    inputPromptText: function (value) {
      if (isNull(value) && isNull(this.$refs.inputField)) {
        return;
      }

      var fieldUpdater = function () {
        this.userInput = '';
        if (!isNull(value) && this.$refs.inputField) {
          this.$refs.inputField.focus();
        }
      }.bind(this);

      if (this.$refs.inputField) {
        fieldUpdater();
      } else {
        this.$nextTick(fieldUpdater);
      }
    },

    logChunks: {
      immediate: true,
      // deep: the store appends log chunks in place (logChunks.push), so the
      // array reference doesn't change. Vue 3 non-deep watchers compare by
      // reference and would never fire on append (Vue 2 fired anyway via its
      // isObject special-case). Without this, streamed output never reaches the
      // log panel. The handler stays incremental via nextLogIndex.
      deep: true,
      handler(newValue, oldValue) {
        const updateLog = () => {
          if (isNull(newValue)) {
            this.setLog('');
            this.nextLogIndex = 0;

            return;
          }

          if (newValue !== oldValue) {
            this.setLog('');
            this.nextLogIndex = 0;
          }

          for (; this.nextLogIndex < newValue.length; this.nextLogIndex++) {
            const logChunk = newValue[this.nextLogIndex];

            this.appendLog(logChunk);
          }
        }

        if (isNull(this.$refs.logPanel)) {
          this.$nextTick(updateLog);
        } else {
          updateLog();
        }
      }
    },

    preloadOutput: {
      handler(newValue, _) {
        this.$nextTick(() => {
          if (this.$refs.preloadOutputPanel) {
            this.$refs.preloadOutputPanel.setLog(newValue);
          }
        })
      }
    },

    inlineImages: {
      // deep: the store adds inline images in place (state.inlineImages[path] = url),
      // so the object reference doesn't change. Like logChunks, a Vue 3 non-deep
      // watcher would never fire on this mutation and images would never render.
      deep: true,
      handler(newValue, oldValue) {
        const logPanel = this.$refs.logPanel;

        forEachKeyValue(this.lastInlineImages, (key, value) => {
          if (!newValue.hasOwnProperty(key)) {
            logPanel.removeInlineImage(key);
          } else if (value !== newValue[key]) {
            logPanel.setInlineImage(key, value);
          }
        });

        forEachKeyValue(newValue, (key, value) => {
          if (!this.lastInlineImages.hasOwnProperty(key)) {
            logPanel.setInlineImage(key, value);
          }
        });

        this.lastInlineImages = deepCloneObject(newValue);
      }
    },

    scriptConfig: {
      immediate: true,
      handler() {
        this.shownErrors = []

        this.$nextTick(() => {
          // 200 is a rough height for headers,buttons, description, etc.
          const otherElemsHeight = 200;

          if (isNull(this.$refs.parametersView)) {
            this.scriptConfigComponentsHeight = otherElemsHeight;
            return;
          }

          const paramHeight = this.$refs.parametersView.$el.clientHeight;

          this.scriptConfigComponentsHeight = paramHeight + otherElemsHeight;
        })
      }
    },

    status: {
      handler(newStatus) {
        if (newStatus === STATUS_FINISHED) {
          this.$store.dispatch('executions/' + this.currentExecutor.state.id + '/cleanup');
        }
      }
    }
  }
}
</script>

<style scoped>

.script-view {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;


  /* (firefox)
      we have to specify min-size explicitly, because by default it's content size.
      It means, that when child content is larger than parent, it will grow out of parent
      See https://drafts.csswg.org/css-flexbox/#min-size-auto
      and https://bugzilla.mozilla.org/show_bug.cgi?id=1114904
  */
  min-height: 0;
}

.actions-panel,
.files-download-panel {
  flex: 0 0 content;
}

.script-description,
.script-loading-text {
  margin: 0;
}

.actions-panel {
  margin-top: 8px;
  display: flex;
}

.actions-panel > .button-gap {
  flex: 3 1 1px;
}

.button-execute {
  flex: 4 1 312px;
}

.button-stop {
  margin-left: 16px;
  flex: 1 1 104px;
}

.schedule-button {
  margin-left: 32px;
  flex: 1 0 auto;
}

.script-input-panel {
  margin-top: 20px;
  margin-bottom: 0;
}

.validation-panel {
  overflow-y: auto;
  flex: 1;

  margin: 20px 0 8px;
}

.validation-panel .header {
  padding-left: 0;
}

.validation-errors-list {
  margin-left: 12px;
  margin-top: 8px;
}

.validation-errors-list li {
  color: #F44336;
}

.files-download-panel {
  margin-top: 12px;
}

.files-download-panel :deep(.v-btn) {
  margin-right: 8px;
  text-transform: none;
}

.script-view :deep(.log-panel) {
  margin-top: 12px;
}

</style>
