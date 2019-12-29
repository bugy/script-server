<template>
    <ExecutionsLogPage/>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import ExecutionsLogPage from '../../history/executions-log-page';

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