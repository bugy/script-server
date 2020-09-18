import {isEmptyArray, isEmptyString, isNull} from '@/common/utils/common';
import axios from 'axios';
import clone from 'lodash/clone';
import get from 'lodash/get';
import scriptExecutor, {STATUS_EXECUTING, STATUS_FINISHED, STATUS_INITIALIZING} from './scriptExecutor';
import {parametersToFormData} from "@/main-app/store/mainStoreHelper";

export const axiosInstance = axios.create();

export default {
    namespaced: true,

    state: {
        currentExecutor: null,
        executors: {}
    },

    mutations: {
        ADD_EXECUTOR(state, executor) {
            state.executors[executor.state.id] = executor;
        },
        SELECT_EXECUTOR(state, executor) {
            state.currentExecutor = executor;
        },
        REMOVE_EXECUTOR(state, executor) {
            delete state.executors[executor.state.id];

            if (state.currentExecutor === executor) {
                state.currentExecutor = null;
            }
        }
    },

    getters: {
        activeExecutors: state => {
            const executors = Object.keys(state.executors).map(e => state.executors[e]);

            return executors.filter(value => {
                return (value.state.status === STATUS_EXECUTING)
                    || (value.state.status === STATUS_INITIALIZING)
            });
        },

        hasActiveExecutors: (state, getters) => {
            return !isEmptyArray(getters.activeExecutors);
        }
    },

    actions: {
        init({state, commit, dispatch}) {
            const store = this;

            axiosInstance.get('executions/active')
                .then(({data: activeExecutionIds}) => {
                    activeExecutionIds.sort((a, b) => parseInt(a) - parseInt(b));

                    const requests = [];

                    for (let i = 0; i < activeExecutionIds.length; i++) {
                        const executionId = activeExecutionIds[i];

                        requests.push(axiosInstance.get('executions/config/' + executionId)
                            .then((({data: executionConfig}) => {
                                const executor = scriptExecutor(executionId, executionConfig.scriptName, executionConfig.parameterValues);

                                store.registerModule(['executions', executionId], executor);
                                store.dispatch('executions/' + executionId + '/reconnect');

                                commit('ADD_EXECUTOR', executor);

                                return executor;
                            })));
                    }

                    if (!isNull(state.currentExecutor) || isNull(store.state.scripts.selectedScript)) {
                        return;
                    }

                    axios.all(requests)
                        .then(axios.spread((...executors) => {
                            if (!isNull(state.currentExecutor) || isNull(store.state.scripts.selectedScript)) {
                                return;
                            }

                            const selectedScript = store.state.scripts.selectedScript;

                            for (const executor of executors) {
                                if (selectedScript === executor.state.scriptName) {
                                    dispatch('selectExecutor', executor);
                                    break;
                                }
                            }
                        }))
                        .catch(e => console.log(e));
                })

        },

        selectScript({state, commit, dispatch}, {selectedScript}) {
            let selectedExecutor = null;

            const matchingExecutors = Object.values(state.executors).filter(function (executor) {
                return (executor.state.scriptName === selectedScript);
            });

            if (!isEmptyArray(matchingExecutors)) {
                matchingExecutors.sort((a, b) => parseInt(a.state.id) - parseInt(b.state.id));
                selectedExecutor = matchingExecutors[0];
            }

            dispatch('selectExecutor', selectedExecutor);
        },

        startExecution({rootState, commit, dispatch}) {
            const store = this;

            const parameterValues = clone(rootState.scriptSetup.parameterValues);
            const scriptName = rootState.scriptConfig.scriptConfig.name;

            const formData = parametersToFormData(parameterValues);
            formData.append('__script_name', scriptName);

            const executor = scriptExecutor(null, scriptName, parameterValues);
            store.registerModule(['executions', 'temp'], executor);
            store.dispatch('executions/temp/setInitialising');

            dispatch('selectExecutor', executor);

            axiosInstance.post('executions/start', formData)
                .then(({data: executionId}) => {
                    store.unregisterModule(['executions', 'temp']);
                    store.registerModule(['executions', executionId], executor);

                    store.dispatch('executions/' + executionId + '/start', executionId);
                    store.dispatch('executions/' + executionId + '/reconnect');

                    commit('ADD_EXECUTOR', executor);

                })
                .catch(error => {
                    const status = get(error, 'response.status');
                    let data = get(error, 'response.data');
                    if (isNull(error.response) || isEmptyString(data)) {
                        data = 'Connection error. Please contact the system administrator';
                    }

                    store.dispatch('executions/temp/setErrorStatus');

                    if (status !== 401) {
                        store.dispatch('executions/temp/appendLog', '\n\n' + data);
                    }

                    store.unregisterModule(['executions', 'temp']);
                });
        },

        stopAll({getters, dispatch}) {
            const activeExecutors = getters.activeExecutors;
            if (isEmptyArray(activeExecutors)) {
                return Promise.resolve();
            }

            return new Promise((resolve, reject) => {
                let message;
                if (activeExecutors.length === 1) {
                    message = 'Some script is running. Do you want to abort it?'
                } else {
                    message = activeExecutors.length + ' scripts are running. Do you want to abort them?'
                }

                const abort = confirm(message);
                if (abort === true) {
                    const abortPromises = activeExecutors.map(executor => dispatch(executor.state.id + '/abort'));
                    Promise.all(abortPromises)
                        .catch(error => console.log('Failed to stop an executor: ' + error))
                        .finally(() => {
                            let retries = 0;
                            const intervalId = setInterval(waitForStop, 50);

                            function waitForStop() {
                                if ((retries > 20) || (!getters.hasActiveExecutors)) {
                                    resolve();
                                    clearInterval(intervalId);
                                }
                                retries++;
                            }
                        });
                } else {
                    reject();
                }
            });
        },

        selectExecutor({commit, state, dispatch}, executor) {
            const currentExecutor = state.currentExecutor;
            if (!isNull(currentExecutor)) {
                // Don't remove finished executor automatically, if it was cleaned up
                // unless id is null, meaning it was an error
                if (executor && !isNull(executor.state.id) && (executor.state.id === currentExecutor.state.id)) {
                    return;
                }

                if (currentExecutor.state.status === STATUS_FINISHED) {
                    dispatch('_removeExecutor', currentExecutor);
                }
            }

            commit('SELECT_EXECUTOR', executor);
            if (executor) {
                dispatch('scriptSetup/setParameterValues', {
                    values: executor.state.parameterValues,
                    forceAllowedValues: true,
                    scriptName: executor.state.scriptName
                }, {root: true});
            }
        },

        _removeExecutor({dispatch, state, commit}, executor) {
            if (!(executor.state.id in state.executors)) {
                return;
            }

            this.unregisterModule(['executions', executor.state.id]);
            commit('REMOVE_EXECUTOR', executor)
        }
    }
}