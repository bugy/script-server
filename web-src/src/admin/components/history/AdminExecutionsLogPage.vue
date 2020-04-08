<template>
    <ExecutionsLogPage/>
</template>

<script>
    import ExecutionsLogPage from '@/common/components/history/executions-log-page';
    import {mapActions, mapState} from 'vuex';

    export default {
        name: 'AdminExecutionsLogPage',
        components: {ExecutionsLogPage},

        computed: {
            ...mapState('history', ['selectedExecution'])
        },

        methods: {
            ...mapActions(['setSubheader'])
        },

        watch: {
            selectedExecution: {
                immediate: true,
                handler(execution) {
                    if (execution) {
                        this.setSubheader('#' + execution.id + ' - ' + execution.user + '@' + execution.script);
                    } else {
                        this.setSubheader(null);
                    }
                }
            }
        }

    }
</script>

<style scoped>

</style>