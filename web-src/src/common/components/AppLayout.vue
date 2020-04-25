<template>
    <div class="app-layout">
        <div :class="{collapsed: !showSidebar}" class="app-sidebar" ref="appSidebar">
            <slot name="sidebar"/>
        </div>
        <div class="app-content">
            <div :class="{borderless: !hasHeader || loading, 'drop-shadow': loading}"
                 class="content-header" ref="contentHeader">
                <a @click="setSidebarVisibility(true)" class="btn-flat app-menu-button">
                    <i class="material-icons">menu</i>
                </a>
                <slot name="header"/>
                <div class="progress" v-if="loading">
                    <div class="indeterminate"></div>
                </div>
            </div>
            <div class="content-panel" ref="contentPanel">
                <slot name="content"/>
            </div>
        </div>
        <div @click="setSidebarVisibility(false)" class="sidenav-overlay" v-show="showSidebar"></div>
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

        border-right: 1px solid #C8C8C8;

        box-shadow: 7px 0 8px -4px #888888;
        -webkit-box-shadow: 7px 0 8px -4px #888888;
        -moz-box-shadow: 7px 0 8px -4px #888888;
    }

    .app-content {
        flex: 1 1 0;

        display: flex;
        flex-direction: column;
    }

    .app-menu-button {
        display: none;

        float: left;
        position: relative;
        z-index: 1;
        margin-right: 8px;
        margin-top: 12px;
        text-align: center;
    }

    .app-menu-button:hover {
        background: none;
    }

    .app-menu-button > i {
        font-size: 2rem;
        line-height: 1;
    }

    @media (max-width: 992px) {
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
        }

        .app-menu-button {
            display: block;
        }
    }

    .content-header {
        flex: 0 0 auto;
        z-index: 1;

        border-bottom: 1px solid #C8C8C8;
        position: relative;
    }

    .content-header.drop-shadow {
        box-shadow: 2px 2px 4px 0 rgba(0, 0, 0, 0.3);
    }

    .content-header.borderless {
        border-bottom: none;
    }

    .content-header .progress {
        margin: 0;
        bottom: 0;
        position: absolute;
    }

    .content-panel {
        flex: 1 1 0;
    }
</style>