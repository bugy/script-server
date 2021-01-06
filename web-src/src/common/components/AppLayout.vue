<template>
  <div class="app-layout">
    <div ref="appSidebar" :class="{collapsed: !showSidebar}" class="app-sidebar shadow-8dp">
      <slot name="sidebar"/>
    </div>
    <div class="app-content">
      <div ref="contentHeader"
           :class="{borderless: !hasHeader, 'shadow-8dp': hasHeader}" class="content-header">
        <a class="btn-flat app-menu-button" @click="setSidebarVisibility(true)">
          <i class="material-icons">menu</i>
        </a>
        <slot name="header"/>
        <div v-if="loading" class="progress">
          <div class="indeterminate"></div>
        </div>
      </div>
      <div ref="contentPanel" class="content-panel">
        <slot name="content"/>
      </div>
    </div>
    <div v-show="showSidebar" class="sidenav-overlay" @click="setSidebarVisibility(false)"></div>
  </div>
</template>

<script>

import {hasClass, isNull} from '@/common/utils/common';

export default {
  name: 'AppLayout',
  props: {
    loading: Boolean
  },
  data() {
    return {
      narrowView: false,
      showSidebar: false,
      hasHeader: false
    }
  },
  mounted() {
    const contentHeader = this.$refs.contentHeader;
    const contentPanel = this.$refs.contentPanel;

    updatedStylesBasedOnContent(contentHeader, contentPanel, this);

    const sidebarStyle = getComputedStyle(this.$refs.appSidebar);

    const resizeListener = () => {
      const position = sidebarStyle.position;
      if (!this.narrowView) {
        this.setSidebarVisibility(false);
      }
      this.narrowView = position === 'absolute';
    };
    window.addEventListener('resize', resizeListener);
    resizeListener();
  },

  methods: {
    setSidebarVisibility(visible) {
      this.showSidebar = visible;
    }
  }
}

function recalculateHeight(contentHeader, appLayout, contentPanel) {
  if (!contentHeader.childNodes) {
    return;
  }

  let childrenHeight = 0;
  for (const child of Array.from(contentHeader.childNodes)) {
    if (hasClass(child, 'app-menu-button')) {
      continue;
    }

    if ((child.nodeType === 1) && (window.getComputedStyle(child).position === 'absolute')) {
      continue;
    }

    if (!isNull(child.offsetHeight)) {
      childrenHeight = Math.max(childrenHeight, child.offsetHeight);
    }
  }
  appLayout.hasHeader = childrenHeight >= 1;

  appLayout.$nextTick(() => {
    contentPanel.style.maxHeight = 'calc(100% - ' + contentHeader.offsetHeight + 'px)';
  });
}

function updatedStylesBasedOnContent(contentHeader, contentPanel, appLayout) {
  const mutationObserver = new MutationObserver(mutations => {
    mutations.forEach(() => {
      recalculateHeight(contentHeader, appLayout, contentPanel);
    });
  });

  mutationObserver.observe(contentHeader, {
    childList: true,
    subtree: true,
    characterData: true
  });

  appLayout.$nextTick(() => {
    recalculateHeight(contentHeader, appLayout, contentPanel);
  });
}

</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  max-height: 100vh;
}

.app-sidebar {
  width: 300px;
  min-width: 300px;

  border-right: 1px solid var(--separator-color);
}

.app-content {
  flex: 1 1 0;

  display: flex;
  flex-direction: column;

  width: 100vw;
}

.app-menu-button {
  display: none;

  float: left;
  position: relative;
  z-index: 1;
  margin-top: 12px;
  text-align: center;
  color: var(--font-color-main);
}

.app-menu-button:hover {
  background: none;
}

.app-menu-button > i {
  font-size: 2rem;
  line-height: 1;
}

.content-header {
  flex: 0 0 auto;
  width: 100%;

  padding-left: 24px;

  border-bottom: 1px solid var(--separator-color);
  position: relative;

  background: var(--script-header-background);
}

.content-header.borderless {
  border-bottom: none;
}

.content-header .progress {
  margin: 0;
  bottom: -1px;
  position: absolute;
  left: 0;
}

.content-panel {
  flex: 1 1 0;
}

@media (max-width: 992px) {
  .content-header {
    padding-left: 0;
  }

  .app-sidebar {
    position: absolute;
    height: 100vh;
    z-index: 999;
    transition: transform 0.3s;
  }

  .app-sidebar.collapsed {
    -webkit-transform: translateX(-105%);
    transform: translateX(-105%);
  }

  .sidenav-overlay {
    opacity: 1;
    display: block;
    background-color: rgba(0, 0, 0, 0.4);
    position: absolute;
    z-index: 500;
    width: 100%;
    height: 100%;
  }

  .app-menu-button {
    display: block;
    margin-right: 12px;
  }
}
</style>