<template>
  <div class="admin-page">
    <div class="page-title primary-color-dark">
      <div class="main-header">
        <v-btn
          icon="home"
          variant="text"
          color="white"
          href="index.html"
          class="home-button"
        />
        <v-tabs color="white" class="admin-tabs">
          <v-tab to="/logs">Logs</v-tab>
          <v-tab to="/scripts">Scripts</v-tab>
        </v-tabs>
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
  align-items: center;
}

.admin-tabs {
  max-width: 30em;
}

:deep(.admin-tabs .v-tab) {
  font-size: 1em;
  font-weight: 500;
  letter-spacing: 1px;
}

.home-button {
  flex-shrink: 0;
  margin: 0 4px;
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
</style>
