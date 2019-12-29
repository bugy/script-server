<template>
    <div class="container">
        <PageProgress v-if="loading"/>
        <executions-log-table :rowClick="goToLog" :rows="executionRows" v-else/>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import ExecutionsLogTable from './executions-log-table'
    import PageProgress from '../components/PageProgress';

    export default {
        name: 'executions-log',

        components: {
            'executions-log-table': ExecutionsLogTable,
            PageProgress
        },

        mounted: function () {
            this.init();
        },

        methods: {
            ...mapActions('history', ['init']),

            goToLog(execution_entry) {
                this.$router.push({
                    path: this.$router.history.current.path + '/' + execution_entry.id
                });
            }
        },

        computed: {
            ...mapState('history', {
                executionRows: 'executions',
                loading: 'loading'
            })
        }
    }


</script>

<style scoped>
    div.executions-log {
        height: 100%;
    }

    div.progress {
        top: 45%;
    }

    div.indeterminate {
        max-width: 480px;
    }
</style>