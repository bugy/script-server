<template>
    <div class="app-history-panel">
        <ExecutionsLogPage :disableProgressIndicator="true" class="main-app-executions-log"/>
    </div>
</template>

<script>
    import ExecutionsLogPage from '@/common/components/history/executions-log-page';
    import {mapActions, mapState} from 'vuex';

    export default {
        name: 'AppHistoryPanel',
        components: {ExecutionsLogPage},
        methods: {
            ...mapActions('page', ['setLoading']),
            updateLoadingIndicator() {
                if (this.$route.params.executionId) {
                    this.setLoading(this.detailsLoading);
                } else {
                    this.setLoading(this.loading);
                }
            }
        },
        computed: {
            ...mapState('history', ['loading', 'detailsLoading'])
        },
        watch: {
            loading: {
                immediate: true,
                handler() {
                    this.updateLoadingIndicator()
                }
            },
            detailsLoading: {
                immediate: true,
                handler() {
                    this.updateLoadingIndicator()
                }
            }
        }
    }

</script>

<style scoped>
    .app-history-panel {
        height: 100%;
        overflow-y: auto;

        background: white;
        padding-bottom: 12px;

        display: flex;
        flex-direction: column;
    }

    .main-app-executions-log {
        height: 100%;
    }
</style>