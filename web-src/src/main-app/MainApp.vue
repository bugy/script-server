<template xmlns:v-slot="http://www.w3.org/1999/XSL/Transform">
  <div id="main-app">
    <AppLayout ref="appLayout" :loading="pageLoading">
      <template v-slot:sidebar>
        <MainAppSidebar/>
      </template>
      <template v-slot:header>
        <router-view name="header"/>
      </template>
      <template v-slot:content>
        <router-view/>
      </template>
    </AppLayout>
    <DocumentTitleManager/>
    <FaviconManager/>
  </div>
</template>

<script>
import '@/assets/css/index.css';
import AppLayout from '@/common/components/AppLayout';
import {isEmptyString} from '@/common/utils/common';
import AppWelcomePanel from './components/AppWelcomePanel';
import DocumentTitleManager from './components/DocumentTitleManager';
import FaviconManager from './components/FaviconManager';
import MainAppSidebar from './components/MainAppSidebar';
import MainAppContent from './components/scripts/MainAppContent';
import {usePageStore} from '@/main-app/stores/page'
import {useAuthStore} from '@/common/stores/auth'
import {useServerConfigStore} from '@/main-app/stores/serverConfig'
import {useScriptsStore} from '@/main-app/stores/scripts'
import {useExecutionsStore} from '@/main-app/stores/executions'

export default {
  name: 'App',
  components: {
    AppLayout,
    MainAppSidebar,
    MainAppContent,
    AppWelcomePanel,
    DocumentTitleManager,
    FaviconManager
  },
  computed: {
    pageLoading() {
      return usePageStore().pageLoading
    }
  },

  created() {
    useAuthStore().init()
    useServerConfigStore().init()
    useScriptsStore().init()
    useExecutionsStore().init()
  },

  mounted() {
    const currentPath = this.$router.currentRoute.value.path;
    this.$refs.appLayout.setSidebarVisibility(isEmptyString(currentPath) || (currentPath === '/'));

    this.$router.afterEach((to) => {
      this.$refs.appLayout.setSidebarVisibility(false);
    });
  }
}
</script>

<style>
h1, h2, h3, h4, h5, h6 {
  margin: 0;
}
</style>