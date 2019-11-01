<template>
    <div class="execution-details container">
        <div>
            <readonly-field class="readonly-field" title="Script name" :value="script"></readonly-field>
            <readonly-field class="readonly-field" title="User" :value="user"></readonly-field>
            <readonly-field class="readonly-field" title="Start time" :value="startTime"></readonly-field>
            <readonly-field class="readonly-field" title="Status" :value="fullStatus"></readonly-field>
            <readonly-field class="long readonly-field" title="Command" :value="command"></readonly-field>
        </div>
        <log-panel class="log-panel" ref="logPanel" :autoscrollEnabled="false"></log-panel>
    </div>
</template>

<script>
    import axios from 'axios';
    import {mapActions, mapGetters} from 'vuex';
    import {isNull} from '../../common';
    import LogPanel from '../../components/log_panel';
    import ReadOnlyField from '../../components/readonly-field';
    import {translateExecutionLog} from './executions-module';

    export default {
        name: 'execution-details',

        data: function () {
            return {
                script: '',
                user: '',
                startTime: '',
                fullStatus: '',
                command: ''
            };
        },

        components: {
            'readonly-field': ReadOnlyField,
            'log-panel': LogPanel
        },

        methods: {
            ...mapActions(['setSubheader']),

            updateSubheaderFromLog(execution) {
                const subheader = '#' + execution.id + ' - ' + execution.user + '@' + execution.script;
                this.setSubheader(subheader);
            }
        },

        computed: {
            ...mapGetters('executions', {
                findExecution: 'findById'
            })
        },

        watch: {
            '$route.params.executionId': {
                immediate: true,
                handler(executionId) {
                    let execution = this.findExecution(executionId);
                    if (isNull(execution)) {
                        execution = {
                            id: executionId,
                            user: 'Unknown',
                            script: 'Unknown'
                        }
                    }
                    this.updateSubheaderFromLog(execution);

                    axios.get('admin/execution_log/long/' + executionId).then(({data: incomingLog}) => {
                        const executionLog = translateExecutionLog(incomingLog);

                        this.script = executionLog.script;
                        this.user = executionLog.user;
                        this.startTime = executionLog.startTimeString;
                        this.fullStatus = executionLog.fullStatus;
                        this.command = executionLog.command;
                        this.$refs.logPanel.setLog(executionLog.log);

                        this.updateSubheaderFromLog(executionLog);
                    });
                }
            }
        }
    }
</script>

<style scoped>
    .execution-details {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .readonly-field {
        margin-top: 6px;
        margin-bottom: 16px;

        display: inline-block;
        width: 200px;
    }

    .readonly-field.long {
        width: 600px;
        max-width: 100%;
    }

    .log-panel {
        margin-top: 4px;
    }
</style>