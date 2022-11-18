<template>
  <div class="container scripts-list">
    <PageProgress v-if="loading"/>
    <div v-else>
      <router-link :to="newScriptPath" append class="waves-effect waves-light btn add-script-btn">
        <i class="material-icons left">add</i>
        Add
      </router-link>
      <div class="collection">

        <template v-for="script in scripts">
          <router-link :key="script.name"
                       :class="{'parsing-failed': script.parsingFailed}"
                       :to="script.path"
                       append
                       class="collection-item">
            {{ script.name }}
          </router-link>
        </template>

      </div>
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

.scripts-list .collection-item.parsing-failed {
  color: var(--error-color);
  pointer-events: none;
}

.scripts-list .collection-item.parsing-failed::after {
  content: '(failed to parse config file)';
}

</style>