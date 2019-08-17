<template>
    <div class="app-layout">
        <div class="app-sidebar">
            <slot name="sidebar"/>
        </div>
        <div class="app-content">
            <div class="content-header" ref="contentHeader">
                <slot name="header"/>
            </div>
            <div class="content-panel" ref="contentPanel">
                <slot name="content"/>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'AppLayout',

        mounted() {
            const contentHeader = this.$refs.contentHeader;
            const contentPanel = this.$refs.contentPanel;

            this.$nextTick(function () {
                let headerHeight = contentHeader.offsetHeight;
                contentPanel.style.maxHeight = 'calc(100% - ' + headerHeight + 'px)';

                if (headerHeight <= 5) {
                    let maxHeight = headerHeight;

                    const mutationObserver = new MutationObserver(function (mutations) {
                        mutations.forEach(function (mutation) {
                            let headerHeight = contentHeader.offsetHeight;
                            if (headerHeight <= maxHeight) {
                                return;
                            }

                            contentPanel.style.maxHeight = 'calc(100% - ' + headerHeight + 'px)';
                            maxHeight = headerHeight;
                        });
                    });

                    mutationObserver.observe(contentHeader, {
                        childList: true,
                        subtree: true,
                        characterData: true
                    })
                }
            })
        }
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
        flex: 1 1 auto;

        display: flex;
        flex-direction: column;
    }

    @media (max-width: 992px) {
        .app-content {
            border-left: none;
        }
    }

    .content-header {
        flex: 0 0 auto;

        border-bottom: 1px solid #C8C8C8;
    }

    .content-panel {
        flex: 1 1 auto;
    }
</style>