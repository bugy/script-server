<template>
    <div class="main-app-sidebar">
        <div class="list-header">
            <router-link :title="versionString" class="header server-header" to="/">
                Script server
            </router-link>

            <SearchPanel v-model="searchText"/>

            <div class="header-link">
              <a v-if="adminUser" class="primary-color-text" href="admin.html">
                <i class="material-icons">settings</i>
              </a>
              <a v-else href="https://github.com/bugy/script-server" target="_blank">
                <svg aria-hidden="true" class="svg-icon github-icon" height="20px" viewBox="0 0 16 16" width="20px">
                  <path
                      d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                </svg>
              </a>
            </div>
        </div>

      <ScriptsList :search-text="searchText"/>

      <router-link
          class="waves-effect btn-flat bottom-panel primary-color-text history-button"
          to='/history'>
        History
      </router-link>

      <div v-if="authEnabled" class="logout-panel bottom-panel">
        <span>{{ username }}</span>
        <a class="btn-icon-flat waves-effect logout-button waves-circle" @click="logout">
          <i class="material-icons primary-color-text">power_settings_new</i>
        </a>
      </div>
    </div>
</template>

<script>
import {mapActions, mapState} from 'vuex';
import ScriptsList from './scripts/ScriptsList'
import SearchPanel from './SearchPanel';

export default {
  name: 'MainAppSidebar',
  components: {
    SearchPanel,
    ScriptsList
  },

  data() {
    return {
      searchText: '',
    }
  },

  computed: {
    ...mapState('serverConfig', {
      versionString: state => state.version ? 'v' + state.version : null
    }),
    ...mapState('auth', {
      adminUser: 'admin',
      username: 'username',
      authEnabled: 'enabled'
            })
        },

        methods: {
            ...mapActions(['logout'])
        }
    }
</script>

<style scoped>
    .list-header {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: flex-end;

        border-bottom: 5px solid transparent; /* This is to make the header on the same level as the script header */

        flex-shrink: 0;

        position: relative;
    }

    .server-header {
        flex-grow: 1;
        margin-left: 0.4rem;

        font-size: 1.64rem;
        padding: 0.8rem;
        font-weight: 300;
        line-height: 110%;
      color: var(--font-color-main)
    }

    .main-app-sidebar {
      height: 100%;

      background: var(--background-color);

      display: flex;
      flex-direction: column;
    }

    .header-link {
      margin: 0 1rem;
      display: flex;
      line-height: 0;
    }

    .header-link .svg-icon {
      width: 24px;
      height: 24px;
    }

    .header-link .svg-icon path {
      fill: var(--primary-color)
    }

    .history-button {
      line-height: 3em;
      text-align: center;
    }

    .bottom-panel {
      height: 3em;
      width: 100%;
      border-top: 1px solid var(--separator-color);

      flex-shrink: 0;
    }

    .logout-panel {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
    }

    .logout-button {
      margin-left: 4px;
    }

</style>