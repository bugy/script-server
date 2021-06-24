import {getWebsocketUrl, isNull, isWebsocketClosed} from '@/common/utils/common';
import Vue from 'vue';
import {axiosInstance} from '@/common/utils/axios_utils';

export const STATUS_INITIALIZING = 'initializing';
export const STATUS_EXECUTING = 'executing';
export const STATUS_FINISHED = 'finished';
export const STATUS_DISCONNECTED = 'disconnected';
export const STATUS_ERROR = 'error';

let oneSecDelay = 1000;

export default (id, scriptName, parameterValues) => {

    const internalState = {
        websocket: null
    };

    function isSocketActive() {
        if (isNull(internalState.websocket)) {
            return false;
        }

        return !isWebsocketClosed(internalState.websocket);
    }

    return {
        namespaced: true,

        state: {
            id: id,
            logChunks: [],
            inputPromptText: null,
            downloadableFiles: [],
            inlineImages: {},
            parameterValues: parameterValues,
            status: STATUS_INITIALIZING,
            scriptName: scriptName,

            killIntervalId: null,
            killTimeoutSec: null,
            killEnabled: false
        },

        actions: {
            reconnect({state, dispatch, commit}) {
                dispatch('setStatus', STATUS_EXECUTING);
                attachToWebsocket(internalState, state, commit, dispatch);
            },

            stopExecution({state, commit, dispatch}) {
                if (isNull(state.killIntervalId) && (!state.killEnabled)) {
                    const intervalId = setInterval(() => {
                        dispatch('_tickKillInterval')
                    }, oneSecDelay);

                    commit('SET_KILL_INTERVAL', {id: intervalId, timeoutSec: 5, killEnabled: false});
                }

                return axiosInstance.post('executions/stop/' + state.id);
            },

            _tickKillInterval({state, commit}) {

                if (state.status !== STATUS_EXECUTING) {
                    if (!isNull(state.killIntervalId)) {
                        clearInterval(state.killIntervalId);
                    }
                    commit('SET_KILL_INTERVAL', {id: null, timeoutSec: null, killEnabled: false});
                    return;
                }

                if (state.killTimeoutSec <= 1) {
                    if (!isNull(state.killIntervalId)) {
                        clearInterval(state.killIntervalId);
                    }
                    commit('SET_KILL_INTERVAL', {id: null, timeoutSec: null, killEnabled: true});
                    return;
                }

                commit('DEC_KILL_INTERVAL');
            },

            killExecution({state}) {
                return axiosInstance.post('executions/kill/' + state.id);
            },

            setInitialising({commit, dispatch}) {
                commit('SET_LOG', 'Calling the script...');
                dispatch('setStatus', STATUS_INITIALIZING);
            },

            start({state, dispatch, commit}, executionId) {
                commit('SET_ID', executionId);
                commit('SET_LOG', null);
                dispatch('setStatus', STATUS_EXECUTING);
                attachToWebsocket(internalState, state, commit, dispatch);
            },

            sendUserInput({}, userInput) {
                if (isSocketActive()) {
                    internalState.websocket.send(userInput);
                }
            },

            setErrorStatus({dispatch}) {
                dispatch('setStatus', STATUS_ERROR);
            },

            appendLog({commit}, log) {
                commit('ADD_LOG_CHUNK', log);
            },

            cleanup({state}) {
                axiosInstance.post('executions/cleanup/' + state.id);
            },

            abort({dispatch}) {
                return dispatch('stopExecution');
            },

            setStatus({commit, state}, status) {

                if (!isNull(state.killIntervalId)) {
                    clearInterval(state.killIntervalId);
                    commit('SET_KILL_INTERVAL', {id: null, timeoutSec: null, killEnabled: false})
                }

                commit('SET_STATUS', status);
            }
        },

        mutations: {
            SET_CONFIG(state, {scriptName, parameterValues}) {
                state.parameterValues = parameterValues;
                state.scriptName = scriptName;
            },

            SET_LOG(state, log) {
                if (!log) {
                    state.logChunks = [];
                } else if (Array.isArray(log)) {
                    state.logChunks = log;
                } else {
                    state.logChunks = [log];
                }
            },

            ADD_LOG_CHUNK(state, chunk) {
                state.logChunks.push(chunk);
            },

            SET_PROMPT_TEXT(state, text) {
                state.inputPromptText = text;
            },

            ADD_FILE(state, file) {
                state.downloadableFiles.push(file);
            },

            ADD_INLINE_IMAGE(state, {output_path, download_url}) {
                Vue.set(state.inlineImages, output_path, download_url);
            },

            SET_STATUS(state, status) {
                state.status = status;
            },

            SET_WEBSOCKET(state, websocket) {
                state.websocket = websocket;
            },

            SET_ID(state, id) {
                state.id = id;
            },

            SET_KILL_INTERVAL(state, {id, timeoutSec, killEnabled}) {
                state.killIntervalId = id;
                state.killTimeoutSec = timeoutSec;
                state.killEnabled = killEnabled;
            },

            DEC_KILL_INTERVAL(state) {
                state.killTimeoutSec--;
            }
        }
    }
}

function attachToWebsocket(internalState, state, commit, dispatch) {
    if (!isNull(internalState.websocket)) {
        return;
    }

    const executionId = state.id;

    let websocket;
    try {
        websocket = new WebSocket(getWebsocketUrl('executions/io/' + executionId));
    } catch (e) {
        console.log('Failed to open websocket')
    }

    websocket.addEventListener('message', function (message) {
        const event = JSON.parse(message.data);

        const eventType = event.event;
        const data = event.data;

        if (eventType === 'output') {
            commit('ADD_LOG_CHUNK', data);

        } else if (eventType === 'input') {
            commit('SET_PROMPT_TEXT', data);

        } else if (eventType === 'file') {
            commit('ADD_FILE', {
                'url': data.url,
                'filename': data.filename
            });
        } else if (eventType === 'inline-image') {
            commit('ADD_INLINE_IMAGE', {
                'output_path': data.output_path,
                'download_url': data.download_url
            });
        }
    });

    websocket.addEventListener('close', function (event) {
        let executionFinished = (event.code === 1000);
        if (!executionFinished) {
            axiosInstance.get('executions/status/' + executionId)
                .then(({data: status}) => {
                    if (status === 'finished') {
                        dispatch('setStatus', STATUS_FINISHED);
                    } else {
                        dispatch('setStatus', STATUS_DISCONNECTED);
                    }
                })
                .catch((error) => {
                    console.log('Failed to connect to the server: ' + error);
                    dispatch('setErrorStatus');
                });

        } else {
            dispatch('setStatus', STATUS_FINISHED);
        }
    });


    internalState.websocket = websocket;
}
