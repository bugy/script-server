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
import {NEW_SCRIPT} from '@/admin/stores/scriptConfig';
import {useAdminScriptsStore} from '@/admin/stores/scripts';

export default {
  name: 'ScriptsList',

  components: {PageProgress},

  mounted() {
    useAdminScriptsStore().init()
  },

  data() {
    return {
      newScriptPath: NEW_SCRIPT
    }
  },

  computed: {
    scripts() {
      const raw = useAdminScriptsStore().scripts
      return raw
          ? raw.map(s => ({
            name: s.name,
            path: encodeURIComponent(s.name),
            parsingFailed: s.parsingFailed
          }))
          : []
    },
    loading() {
      return useAdminScriptsStore().loading
    }
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
