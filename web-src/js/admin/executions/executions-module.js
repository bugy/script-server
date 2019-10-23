import axios from 'axios';
import {isNull} from '../../common';

export default {
    state: {
        executions: [],
        loading: false
    },
    namespaced: true,
    actions: {
        init({commit}) {
            commit('SET_LOADING', true);

            axios.get('admin/execution_log/short').then(({data}) => {

                sortExecutionLogs(data);

                let executions = data.map(log => translateExecutionLog(log));
                commit('SET_EXECUTIONS', executions);
                commit('SET_LOADING', false);
            });
        }

    },
    mutations: {
        SET_LOADING(state, loading) {
            state.loading = loading;
        },

        SET_EXECUTIONS(state, executions) {
            state.executions = executions;
        }
    },
    getters: {
        findById: (state) => (id) => {
            return state.executions.find(execution => execution.id === id)
        }
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

        let dateCompare = Date.parse(v2.startTime) - Date.parse(v1.startTime);
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
        const startTime = new Date(log.startTime);
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