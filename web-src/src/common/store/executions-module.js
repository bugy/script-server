import {isEmptyString, isNull, logError} from '@/common/utils/common';
import {axiosInstance} from '@/common/utils/axios_utils';

const store = () => ({
    state: {
        executions: [],
        selectedExecution: null,
        selectedExecutionId: null,
        loading: false,
        detailsLoading: false,
        page: 1,
        pageSize: 25,
        total: 0,
        totalPages: 1,
        pageSizeOptions: [10, 25, 50, 100, 250, 500]
    },
    namespaced: true,
    actions: {
        init({dispatch}) {
            return dispatch('loadExecutions');
        },

        loadExecutions({commit, state}, params = {}) {
            commit('SET_LOADING', true);
            commit('SET_EXECUTION_DETAILS', {execution: null, id: null});

            const page = params.page !== undefined ? params.page : state.page;
            const size = params.size !== undefined ? params.size : state.pageSize;

            return axiosInstance.get('history/execution_log/short', {
                params: {
                    page,
                    size
                }
            }).then(({data}) => {
                let executions = [];
                let paginationData = {};

                if (Array.isArray(data)) {
                    sortExecutionLogs(data);
                    executions = data.map(log => translateExecutionLog(log));
                    paginationData = {
                        page: 1,
                        pageSize: executions.length || size,
                        total: executions.length,
                        totalPages: 1
                    };
                } else if (data && typeof data === 'object') {
                    let records = data.records || [];
                    executions = records.map(log => translateExecutionLog(log));
                    paginationData = {
                        page: data.page || page,
                        pageSize: data.pageSize || size,
                        total: data.total || 0,
                        totalPages: data.totalPages || 1
                    };
                }

                commit('SET_EXECUTIONS', executions);
                commit('SET_PAGINATION', paginationData);
                commit('SET_LOADING', false);
            }).catch((error) => {
                commit('SET_LOADING', false);
                logError(error);
            });
        },

        changePage({dispatch, state}, newPage) {
            if (newPage < 1 || (state.totalPages > 0 && newPage > state.totalPages)) {
                return;
            }
            return dispatch('loadExecutions', {page: newPage, size: state.pageSize});
        },

        changePageSize({dispatch}, newSize) {
            return dispatch('loadExecutions', {page: 1, size: newSize});
        },

        selectExecution({commit, state}, executionId) {
            if (isEmptyString(executionId)) {
                commit('SET_EXECUTION_DETAILS', {id: executionId, execution: null});
                commit('SET_DETAILS_LOADING', false);
                return;
            }

            let execution = findById(state.executions, executionId);
            if (isNull(execution)) {
                execution = {
                    id: executionId,
                    user: 'Unknown',
                    script: 'Unknown'
                };
            }
            commit('SET_EXECUTION_DETAILS', {id: executionId, execution});
            commit('SET_DETAILS_LOADING', true);

            axiosInstance.get('history/execution_log/long/' + executionId).then(({data: incomingLog}) => {
                if (executionId !== state.selectedExecutionId) {
                    return;
                }

                const executionLog = translateExecutionLog(incomingLog);

                commit('SET_EXECUTION_DETAILS', {id: executionId, execution: executionLog});
                commit('SET_DETAILS_LOADING', false);
            }).catch((error) => {
                logError(error);
            });
        }
    },
    mutations: {
        SET_LOADING(state, loading) {
            state.loading = loading;
        },

        SET_EXECUTIONS(state, executions) {
            state.executions = executions;
        },

        SET_PAGINATION(state, {page, pageSize, total, totalPages}) {
            if (page !== undefined) state.page = page;
            if (pageSize !== undefined) state.pageSize = pageSize;
            if (total !== undefined) state.total = total;
            if (totalPages !== undefined) state.totalPages = totalPages;
        },

        SET_EXECUTION_DETAILS(state, {execution, id}) {
            state.selectedExecution = execution;
            state.selectedExecutionId = id;
        },

        SET_DETAILS_LOADING(state, loading) {
            state.detailsLoading = loading;
        }
    }
});

export default store

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

function findById(executions, id) {
    return executions.find(execution => execution.id === id)
}
