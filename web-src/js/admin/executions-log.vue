<template>
    <div class="container">
        <executions-log-table :rows="executionRows" :rowClick="goToLog"></executions-log-table>
    </div>
</template>

<script>
    import ExecutionsLogTable from './executions-log-table'
    import {callHttp, isNull} from '../common';

    export default {
        name: 'executions-log',

        components: {
            'executions-log-table': ExecutionsLogTable
        },

        mounted: function () {
            callHttp('admin/execution_log/short', null, 'GET', function (rawLogs) {
                var logs = JSON.parse(rawLogs);
                var rows = [];

                sortExecutionLogs(logs);

                for (var i = 0; i < logs.length; i++) {
                    var log = logs[i];

                    rows.push(translateExecutionLog(log));
                }
                this.executionRows = rows;
            }.bind(this));
        },

        methods: {
            goToLog(execution_entry) {
                this.$store.commit('selectExecution', execution_entry);
                this.$router.push({
                    path: this.$router.history.current.path + '/' + execution_entry.id
                });
            }
        },

        data: function () {
            return {
                executionRows: []
            };
        }
    }

    function sortExecutionLogs(logs) {
        logs.sort(function (v1, v2) {
            if (isNull(v1.startTime)) {
                if (isNull(v2.startTime)) {
                    return v1.user.localeCompare(v2.user);
                }
                return 1;
            } else if (isNull(v2.startTime)) {
                return -1;
            }

            var dateCompare = Date.parse(v2.startTime) - Date.parse(v1.startTime);
            if (dateCompare !== 0) {
                return dateCompare;
            }

            return v1.user.localeCompare(v2.user);
        });
    }

    export function translateExecutionLog(log) {
        log.startTimeString = getStartTimeString(log);
        log.fullStatus = getFullStatus(log);

        return log;
    }

    function getStartTimeString(log) {
        if (!isNull(log.startTime)) {
            var startTime = new Date(log.startTime);
            return startTime.toLocaleDateString() + ' ' + startTime.toLocaleTimeString();
        } else {
            return '';
        }
    }

    function getFullStatus(log) {
        if (!isNull(log.exitCode) && !isNull(log.status)) {
            return log.status + ' (' + log.exitCode + ')'
        } else if (!isNull(log.status)) {
            return log.status;
        }
    }
</script>
