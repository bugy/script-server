<template>
    <div class="executions-log page section">
        <router-view/>
    </div>
</template>

<script>
    import ExecutionDetails from './execution-details';
    import ExecutionsLog from './executions-log';

    export default {
        name: 'executions-log-page'
    }

    export const routerChildren = [
        {path: '', component: ExecutionsLog},
        {path: ':executionId', component: ExecutionDetails, props: true}
    ];

</script>

<style scoped>

</style>
