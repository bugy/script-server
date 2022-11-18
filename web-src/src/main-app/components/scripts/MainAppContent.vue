<template>
  <div class="main-app-content">
    <ScriptView ref="scriptView" :class="{collapsed: showError}"
                :hideExecutionControls="showError"/>
    <div v-if="showError" class="error-panel">
      <p v-if="!authenticated">
        Credentials expired, please <a href="javascript:void(0)" onclick="location.reload()">relogin</a>
      </p>
      <p v-else-if="scriptLoadError && notFound">
        Failed to load script info: script '{{ selectedScript }}' not found
      </p>
      <p v-else-if="scriptLoadError && cannotParse">
        Cannot parse script config file, please contact the administrator
      </p>
      <p v-else-if="scriptLoadError">
        Failed to load script info. Try to reload the page. Error message:
        <br>
        {{ scriptLoadError }}
      </p>
    </div>
  </div>
</template>

<script>
import {isEmptyString} from '@/common/utils/common';
import {mapActions, mapState} from 'vuex';
import {CANNOT_PARSE_ERROR_PREFIX, NOT_FOUND_ERROR_PREFIX} from '../../store/scriptConfig';
import ScriptView from './script-view';

export default {
  name: 'MainAppContent',
  components: {ScriptView},

  computed: {
    showError() {
      return !!(this.scriptLoadError || !this.authenticated);
    },
    notFound() {
      return !isEmptyString(this.scriptLoadError) && this.scriptLoadError.startsWith(NOT_FOUND_ERROR_PREFIX);
    },
    cannotParse() {
      return !isEmptyString(this.scriptLoadError) && this.scriptLoadError.startsWith(CANNOT_PARSE_ERROR_PREFIX); 
    },
    ...mapState('auth', ['authenticated']),
    ...mapState('scriptConfig', {scriptLoadError: 'loadError', loading: 'loading'}),
    ...mapState('scripts', ['selectedScript'])
  },
  methods: {
    ...mapActions('page', ['setLoading'])
  },
  watch: {
    loading: {
      immediate: true,
      handler(newValue) {
        this.setLoading(newValue);
      }
    }
  }
}
</script>

<style scoped>
.main-app-content {
  height: 100%;

  background: var(--background-color);
  padding: 16px 24px 12px;

  display: flex;
  flex-direction: column;
}

.main-app-content >>> .input-field label {
  top: 0;

  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.collapsed {
  flex: 0 1 auto;
}

.error-panel {
  color: #F44336;
  margin-top: 17px;
}

.error-panel p {
  margin: 0;
}

</style>