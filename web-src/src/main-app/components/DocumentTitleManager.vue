<template>

</template>

<script>
import {isNull} from '@/common/utils/common';
import {useScriptsStore} from '@/main-app/stores/scripts'
import {useServerConfigStore} from '@/main-app/stores/serverConfig'

const defaultTitle = document.title;

export default {
  name: 'DocumentTitleManager',
  computed: {
    selectedScript() {
      return useScriptsStore().selectedScript
    },
    serverName() {
      return useServerConfigStore().serverName || defaultTitle
    },
    enableScriptTitles() {
      const val = useServerConfigStore().enableScriptTitles
      return isNull(val) || val
    }
  },

  methods: {
    updateTitle() {
      if ((this.enableScriptTitles) && (!isNull(this.selectedScript))) {
        document.title = this.selectedScript + ' - ' + this.serverName;
      } else {
        document.title = this.serverName;
      }
    }
  },

  watch: {
    serverName: function () {
      this.updateTitle();
    },
    selectedScript: function () {
      this.updateTitle();
    },
    enableScriptTitles: function () {
      this.updateTitle();
    }
  }
}
</script>

<style scoped>

</style>