import axios from 'axios';
import {getWebsocketUrl, isNull, isWebsocketClosed} from '../../common';

export const STATUS_INITIALIZING = 'initializing';
export const STATUS_EXECUTING = 'executing';
export const STATUS_FINISHED = 'finished';
export const STATUS_DISCONNECTED = 'disconnected';
export const STATUS_ERROR = 'error';


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
            parameterValues: parameterValues,
            status: STATUS_INITIALIZING,
            scriptName: scriptName
        },

        actions: {
            reconnect({state, dispatch, commit}) {
                commit('SET_STATUS', STATUS_EXECUTING);
                attachToWebsocket(internalState, state, commit);
            },

            stopExecution({state}) {
                return axios.post('executions/stop/' + state.id);
            },

            setInitialising({commit}) {
                commit('SET_STATUS', STATUS_INITIALIZING);
                commit('SET_LOG', 'Calling the script...');
            },

            start({state, commit}, executionId) {
                commit('SET_ID', executionId);
                commit('SET_STATUS', STATUS_EXECUTING);
                commit('SET_LOG', null);
                attachToWebsocket(internalState, state, commit);
            },

            sendUserInput({}, userInput) {
                if (isSocketActive()) {
                    internalState.websocket.send(userInput);
                }
            },

            setErrorStatus({commit}) {
                commit('SET_STATUS', STATUS_ERROR);
            },

            appendLog({commit}, log) {
                commit('ADD_LOG_CHUNK', log);
            },

            cleanup() {
                if (isSocketActive()) {
                    internalState.websocket.close();
                }
            },

            abort({dispatch}) {
                return dispatch('stopExecution')
                    .finally(() => dispatch('cleanup'));
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

            SET_STATUS(state, status) {
                state.status = status;
            },

            SET_WEBSOCKET(state, websocket) {
                state.websocket = websocket;
            },

            SET_ID(state, id) {
                state.id = id;
            }
        }
    }
}

function attachToWebsocket(internalState, state, commit) {
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
        }
    });

    websocket.addEventListener('close', function (event) {
        let executionFinished = (event.code === 1000);
        if (!executionFinished) {
            axios.get('executions/status/' + executionId)
                .then(({status: data}) => {
                    if (data === 'finished') {
                        commit('SET_STATUS', STATUS_FINISHED);
                        axios.post('executions/cleanup/' + executionId);
                    } else {
                        commit('SET_STATUS', STATUS_DISCONNECTED);
                    }
                })
                .catch((error) => {
                    console.log('Failed to connect to the server: ' + error);
                    commit('SET_STATUS', STATUS_ERROR);
                });

        } else {
            commit('SET_STATUS', STATUS_FINISHED);
            axios.post('executions/cleanup/' + executionId);
        }
    });


    internalState.websocket = websocket;
}
