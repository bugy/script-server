<template>
  <div class="script-config">
    <div ref="scriptConfigContent" class="script-config-content">
      <div class="container">
        <div v-if="loadingError" class="error">{{ loadingError }}</div>
        <ScriptConfigForm v-else-if="scriptConfig" v-model="scriptConfig" :original-name="scriptName"/>
        <div v-if="!loadingError && scriptConfig">
          <h5>Parameters</h5>
          <ScriptParamList :parameters="scriptConfig.parameters"/>
        </div>
      </div>
    </div>
    <footer class="page-footer primary-color-dark">
      <div class="footer-left">
        <PromisableButton v-if="scriptName !== NEW_SCRIPT"
                          :click="deleteScript"
                          class="delete-button"
                          icon-text="delete"
                          title="Delete"/>
      </div>

      <PromisableButton :click="save" title="Save"/>

      <div class="footer-right"/>
    </footer>
  </div>
</template>

<script>
import {NEW_SCRIPT, useAdminScriptConfigStore} from '@/admin/stores/scriptConfig';
import PromisableButton from '@/common/components/PromisableButton';
import ParameterConfigForm from './ParameterConfigForm';
import ScriptConfigForm from './ScriptConfigForm';
import ScriptParamList from './ScriptParamList';

export default {
  name: 'ScriptConfig',
  components: {PromisableButton, ScriptParamList, ParameterConfigForm, ScriptConfigForm},
  props: {
    scriptName: {
      type: String
    }
  },

  computed: {
    scriptConfig() {
      return useAdminScriptConfigStore().scriptConfig
    },
    loadingError() {
      return useAdminScriptConfigStore().error
    },
    NEW_SCRIPT() {
      return NEW_SCRIPT
    }
  },

  methods: {
    save() {
      return useAdminScriptConfigStore().save()
    },
    deleteScript() {
      return useAdminScriptConfigStore().deleteScript()
    }
  },

  watch: {
    scriptName: {
      immediate: true,
      handler(scriptName) {
        useAdminScriptConfigStore().init(scriptName)
      }
    }
  }
}
</script>

<style scoped>
.script-config {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.script-config :deep(h5) {
  margin-left: 0.75rem;
  margin-top: 0.5rem;
  margin-bottom: 2rem;
}

.script-config .script-config-content {
  padding-top: 1.5em;
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
}

.script-config .script-config-content .container {
  height: 100%;
}

footer.page-footer {
  padding-top: 0;

  flex: 0 0 0;

  display: flex;
}

.script-config :deep(footer.page-footer .v-btn) {
  height: 48px;
  min-width: 136px;
  font-size: 16px;
}

.script-config .footer-left,
.script-config .footer-right {
  flex: 1 1 0;
}

.script-config :deep(footer.page-footer .v-btn .v-icon) {
  font-size: 24px;
}

</style>