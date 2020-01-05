import axios from 'axios';
import {deepCloneObject, forEachKeyValue, isEmptyArray, isNull} from '../../common';
import scriptExecutor, {STATUS_EXECUTING, STATUS_FINISHED, STATUS_INITIALIZING} from './scriptExecutor';
import * as _ from 'lodash';

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
        init({state, commit}) {
            const store = this;

            axios.get('executions/active')
                .then(({data: activeExecutionIds}) => {
                    for (let i = 0; i < activeExecutionIds.length; i++) {
                        const executionId = activeExecutionIds[i];

                        axios.get('executions/config/' + executionId)
                            .then((({data: executionConfig}) => {
                                const executor = scriptExecutor(executionId, executionConfig.scriptName, executionConfig.parameterValues);

                                store.registerModule(['executions', executionId], executor);
                                store.dispatch('executions/' + executionId + '/reconnect');

                                commit('ADD_EXECUTOR', executor);
                                if (isNull(state.currentExecutor) && store.state.scripts.selectedScript === executionConfig.scriptName) {
                                    commit('SELECT_EXECUTOR', executor);
                                    store.dispatch('scriptSetup/setParameterValues', {
                                        values: deepCloneObject(executionConfig.parameterValues),
                                        forceAllowedValues: true,
                                        scriptName: executionConfig.scriptName
                                    });
                                }
                            }));
                    }
                });
        },

        selectScript({state, commit, dispatch}, {selectedScript}) {
            const store = this;

            let selectedExecutor = null;

            if ((!isNull(state.currentExecutor))) {
                const previousScriptName = state.currentExecutor.state.scriptName;

                const executorsToRemove = Object.values(state.executors).filter(function (executor) {
                    return (executor.state.scriptName === previousScriptName) && executor.state.status === STATUS_FINISHED;
                });

                for (const executor of executorsToRemove) {
                    dispatch(executor.state.id + '/cleanup');
                    store.unregisterModule(['executions', executor.state.id]);
                    commit('REMOVE_EXECUTOR', executor)
                }
            }

            forEachKeyValue(state.executors, (key, value) => {
                if (value.state.scriptName === selectedScript) {
                    selectedExecutor = value;
                }
            });

            commit('SELECT_EXECUTOR', selectedExecutor);
            if (selectedExecutor) {
                dispatch('scriptSetup/setParameterValues', {
                    values: selectedExecutor.state.parameterValues,
                    forceAllowedValues: true,
                    scriptName: selectedScript
                }, {root: true});
            }
        },

        startExecution({rootState, commit}) {
            const store = this;

            const parameterValues = $.extend({}, rootState.scriptSetup.parameterValues);
            const scriptName = rootState.scriptConfig.scriptConfig.name;

            var formData = new FormData();
            formData.append('__script_name', scriptName);

            forEachKeyValue(parameterValues, function (parameter, value) {
                if (Array.isArray(value)) {
                    for (let i = 0; i < value.length; i++) {
                        const valueElement = value[i];
                        formData.append(parameter, valueElement);
                    }
                } else if (!isNull(value)) {
                    formData.append(parameter, value);
                }
            });

            const executor = scriptExecutor(null, scriptName, parameterValues);
            store.registerModule(['executions', 'temp'], executor);
            store.dispatch('executions/temp/setInitialising');

            commit('SELECT_EXECUTOR', executor);

            axios.post('executions/start', formData)
                .then(({data: executionId}) => {
                    store.unregisterModule(['executions', 'temp']);
                    store.registerModule(['executions', executionId], executor);

                    store.dispatch('executions/' + executionId + '/start', executionId);
                    store.dispatch('executions/' + executionId + '/reconnect');

                    commit('ADD_EXECUTOR', executor);

                })
                .catch(error => {
                    const status = _.get(error, 'response.status');
                    let data = _.get(error, 'response.data');
                    if (isNull(error.response)) {
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
        }
    }
}