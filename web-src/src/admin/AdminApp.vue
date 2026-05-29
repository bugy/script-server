<template>
  <div class="admin-page">
    <div class="page-title primary-color-dark">
      <div class="main-header">
        <a class="btn-flat left home-button" href="index.html">
          <i class="material-icons">home</i>
        </a>
        <ul ref="tabs" class="tabs tabs-fixed-width">
          <li class="tab">
            <router-link to="/logs">Logs</router-link>
          </li>
          <li class="tab">
            <router-link to="/scripts">Scripts</router-link>
          </li>
        </ul>
      </div>
      <div v-if="subheader" class="subheader">{{ subheader }}</div>
    </div>
    <router-view class="page-content"/>
  </div>
</template>

<script>
import {mapActions, mapState} from 'vuex';
import File_upload from '@/common/components/file_upload'

export default {
  name: 'AdminApp',
  components: {File_upload},

  mounted() {
    M.Tabs.init(this.$refs.tabs, {});

    this.init()
  },

  computed: {
    ...mapState(['subheader'])
  },

  methods: {
    ...mapActions(['setSubheader']),
    ...mapActions('auth', ['init'])
  },

  watch: {
    $route() {
      this.setSubheader(null);
    }
  }
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;

  background: var(--background-color);
  font-family: "Roboto", sans-serif;
  font-weight: normal;

  height: 100vh;
}

.page-title {
  flex: 0 0 0;
  width: 100%;

  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;

  box-shadow: var(--shadow-4dp);
}

.main-header {
  display: flex;
}

.tabs.tabs-fixed-width {
  max-width: 30em;
  background: none;
}

.tabs.tabs-fixed-width .tab a {
  font-size: 1em;
  font-weight: 500;
  letter-spacing: 1px;
}

.subheader {
  font-size: 1em;
  font-weight: 400;

  text-transform: uppercase;
  text-align: center;
  color: var(--font-on-primary-color-dark-main);

  margin-top: 0.8em;
  margin-bottom: 0.8em;
}

.page-content {
  flex: 1 1 0;
  overflow-y: auto;
}

.home-button {
  height: 100%;
  padding-left: 20px;
  padding-right: 20px;
}

.home-button i {
  font-size: 1.8em;
  line-height: 1.8em;
}
</style>