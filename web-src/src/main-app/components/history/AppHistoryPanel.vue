<template>
    <div class="app-history-panel">
        <ExecutionsLogPage class="main-app-executions-log"/>
    </div>
</template>

<script>
    import ExecutionsLogPage from '@/common/components/history/executions-log-page';

    export default {
        name: 'AppHistoryPanel',
        components: {ExecutionsLogPage}
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