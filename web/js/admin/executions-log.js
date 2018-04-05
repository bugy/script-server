'use strict';

var executionsLogPage;

(function () {
    var pageState = {selectedExecution: null};

    //noinspection JSAnnotator
    Vue.component('executions-log-table', {
        template: `
            <table class="highlight striped executions-log-table">
                <thead>
                    <tr>
                        <th class="start_time-column">Start Time</th>
                        <th class="user-column">User</th>
                        <th class="script-column">Script</th>
                        <th class="status-column">Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="row in rows" :key="row.id" @click="rowClick(row)">
                        <td>{{ row.startTimeString }}</td>
                        <td>{{ row.user }}</td>
                        <td>{{ row.script }}</td>
                        <td>{{ row.fullStatus }}</td>
                    </tr>
                </tbody>
            </table>`,
        props: {
            rows: Array,
            rowClick: {
                type: Function
            }
        }
    });

    //noinspection JSAnnotator
    var executionDetailsComponent = Vue.component('execution-details', {
        template: `
            <div class="execution-details container">
                <div>
                    <readonly-field title="Script name" :value="script"></readonly-field>
                    <readonly-field title="User" :value="user"></readonly-field>
                    <readonly-field title="Start time" :value="startTime"></readonly-field>
                    <readonly-field title="Status" :value="fullStatus"></readonly-field>
                    <readonly-field class="long" title="Command" :value="command"></readonly-field>
                </div>
                <log-panel :log="log" :autoscrollEnabled="false"></log-panel>
            </div>`,

        mounted: function () {
            var executionId = this.$route.params.executionId;
            callHttp('admin/execution_log/long/' + executionId, null, 'GET', function (rawLog) {
                var incomingLog = JSON.parse(rawLog);
                var executionLog = translateExecutionLog(incomingLog);

                this.script = executionLog.script;
                this.user = executionLog.user;
                this.startTime = executionLog.startTimeString;
                this.fullStatus = executionLog.fullStatus;
                this.command = executionLog.command;
                this.log = executionLog.log;

                this.$set(this.pageState, 'selectedExecution', executionLog);

            }.bind(this));
        },

        data: function () {
            return {
                script: '', user: '', startTime: '', fullStatus: '', command: '', log: '',
                pageState: pageState
            };
        }
    });

    //noinspection JSAnnotator
    var executionsLogComponent = Vue.component('executions-log', {
        template: `
        <div class="container">
            <executions-log-table :rows="executionRows" :rowClick="goToLog"></executions-log-table>
        </div>`,

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
                this.$set(this.pageState, 'selectedExecution', execution_entry);
                this.$router.push({
                    path: this.$router.history.current.path + '/' + execution_entry.id
                });
            }
        },

        data: function () {
            return {executionRows: [], pageState: pageState};
        }
    });

    //noinspection JSAnnotator
    executionsLogPage = Vue.component('executions-log-page', {
        template: `
            <div class="executions-log page">
                <div class="page-title teal">
                    <router-link :to="baseRoute" class="breadcrumb">Executions</router-link>
                    <router-link v-if="selectedExecutionString" :to="$route.path" class="breadcrumb">
                        {{ selectedExecutionString }}
                    </router-link>
                </div>
                <div class="section">
                    <router-view></router-view>
                </div>
            </div>`,

        beforeRouteUpdate(to, from, next) {
            next();
            this.routeChanged(to);
        },

        beforeRouteEnter(to, from, next) {
            next(function (self) {
                self.routeChanged(to);
            });
        },

        data: function () {
            return {pageState: pageState};
        },

        methods: {
            routeChanged: function (newRoute) {
                if (isNull(newRoute.params.executionId)) {
                    this.$set(this.pageState, 'selectedExecution', null);
                } else if (isNull(this.pageState.selectedExecution)) {
                    this.$set(this.pageState, 'selectedExecution', {
                        id: newRoute.params.executionId,
                        user: 'unknown',
                        script: 'unknown'
                    });
                }
            }
        },

        computed: {
            baseRoute: function () {
                return this.$route.matched[0].path;
            },
            selectedExecutionString: function () {
                var execution = this.pageState.selectedExecution;
                if (isNull(execution)) {
                    return null;
                }

                return '#' + execution.id + ' - ' + execution.user + '@' + execution.script;
            }
        }
    });

    executionsLogPage.childRoutes = [
        {path: '', component: executionsLogComponent},
        {path: ':executionId', component: executionDetailsComponent}
    ];
})();

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

function translateExecutionLog(log) {
    log.startTimeString = getStartTimeString(log);
    log.fullStatus = getFullStatus(log);

    return log;
}