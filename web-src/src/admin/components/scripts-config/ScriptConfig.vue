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
                          :click="onDeleteScript"
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
import {NEW_SCRIPT} from '@/admin/store/script-config-module';
import PromisableButton from '@/common/components/PromisableButton';
import {mapActions, mapState} from 'vuex';
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

  methods: {
    ...mapActions('scriptConfig', ['init', 'save', 'deleteScript']),
    async onDeleteScript() {
      await this.deleteScript({scriptName: this.scriptName});
    }
  },

  computed: {
    ...mapState('scriptConfig', {
      scriptConfig: 'scriptConfig',
      loadingError: 'error'
    }),
    NEW_SCRIPT() {
      return NEW_SCRIPT;
    }
  },

  watch: {
    scriptName: {
      immediate: true,
      handler(scriptName) {
        this.init(scriptName);
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

.script-config >>> h5 {
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

.script-config >>> footer.page-footer a.btn-flat {
  height: 48px;
  line-height: 48px;
  width: 136px;
  text-align: center;
  font-size: 16px;
}

.script-config .footer-left,
.script-config .footer-right {
  flex: 1 1 0;
}

.script-config >>> footer.page-footer .preloader-wrapper {
  width: 30px;
  height: 30px;
}

.script-config >>> footer.page-footer .spinner-layer {
  border: var(--font-on-primary-color-dark-main);
}

.script-config >>> footer.page-footer .btn-flat i {
  font-size: 24px;
}

</style>