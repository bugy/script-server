<template>
  <div class="container scripts-list">
    <PageProgress v-if="loading"/>
    <div v-else>
      <v-btn
        :to="newScriptPath"
        color="primary"
        prepend-icon="add"
        class="add-script-btn"
      >
        Add
      </v-btn>
      <v-list>
        <v-list-item
          v-for="script in scripts"
          :key="script.name"
          :to="script.parsingFailed ? undefined : script.path"
          :title="script.parsingFailed ? script.name + ' (failed to parse config file)' : script.name"
          :class="{'parsing-failed': script.parsingFailed}"
        />
      </v-list>
    </div>
  </div>
</template>

<script>
import PageProgress from '@/common/components/PageProgress';
import {mapActions, mapState} from 'vuex';
import {NEW_SCRIPT} from '../../store/script-config-module';

export default {
  name: 'ScriptsList',

  mounted: function () {
    this.init();
  },

  data() {
    return {
      newScriptPath: NEW_SCRIPT
    }
  },

  computed: {
    ...mapState('scripts', {
      scripts: state => {
        return state.scripts
            ? state.scripts.map(s => ({
              name: s.name,
              path: encodeURIComponent(s.name),
              parsingFailed: s.parsingFailed
            }))
            : []
      },
      loading: 'loading'
    })
  },

  components: {
    PageProgress
  },

  methods: {
    ...mapActions('scripts', ['init'])
  }
}
</script>

<style scoped>
.scripts-list {
  margin-top: 1.5em;
  margin-bottom: 1em;
}

.add-script-btn {
  margin-bottom: 1em;
}

.parsing-failed :deep(.v-list-item-title) {
  color: var(--error-color);
}

.parsing-failed {
  pointer-events: none;
}
</style>
