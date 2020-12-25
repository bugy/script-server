<template>

</template>

<script>
import {isNull} from '@/common/utils/common';
import {mapState} from 'vuex';

const defaultTitle = document.title;

export default {
  name: 'DocumentTitleManager',
  computed: {
    ...mapState('scripts', {
      selectedScript: 'selectedScript'
    }),
    ...mapState('serverConfig', {
      serverName: state => state.serverName || defaultTitle,
      enableScriptTitles: state => isNull(state.enableScriptTitles) || state.enableScriptTitles
    })
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