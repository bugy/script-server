import {ReactiveWebSocket} from '@/common/connections/rxWebsocket';
import clone from 'lodash/clone';
import {
    forEachKeyValue,
    HttpForbiddenError,
    HttpRequestError,
    HttpUnauthorizedError,
    isEmptyArray,
    isEmptyObject,
    isEmptyString,
    isNull,
    logError,
    removeElement,
    SocketClosedError,
    toDict,
    toQueryArgs
} from '@/common/utils/common';
import {axiosInstance} from '@/common/utils/axios_utils';
import Vue from 'vue';
import {preprocessParameter} from '../utils/model_helper';

const internalState = {
    websocket: null,
    reconnectionAttempt: 0
};

const reconnectionDelay = 500;

function sendParameterValue(parameterName, value, websocket, newStateVersion) {
    const data = {
        parameter: parameterName,
        value,
        clientStateVersion: newStateVersion
    };
    websocket.send(JSON.stringify({
        'event': 'parameterValue',
        data
    }));
}

function sendReloadModelRequest(parameterValues, clientModelId, websocket, newStateVersion) {
    const data = {
        parameterValues,
        clientModelId,
        clientStateVersion: newStateVersion
    };
    websocket.send(JSON.stringify({
        'event': 'reloadModelValues',
        data
    }));
}

export const NOT_FOUND_ERROR_PREFIX = `Failed to find the script`;
export const CANNOT_PARSE_ERROR_PREFIX = `Cannot parse script config file`;

export default () => ({
    state: {
        scriptConfig: null,
        loadError: null,
        parameters: [],
        sentValues: {},
        loading: false,
        clientStateVersion: 0
    },
    namespaced: true,
    actions: {
        reloadScript({state, commit, dispatch}, {selectedScript}) {
            dispatch('setConnection', null);
            commit('RESET_CONFIG');

            if (!isEmptyString(selectedScript)) {
                commit('SET_LOADING', true);
                reconnect(state, internalState, commit, dispatch, selectedScript);
            }
        },

        reloadModel({state, commit, rootState}, {scriptName, parameterValues, clientModelId}) {
            if (rootState.scripts.selectedScript === scriptName) {
                commit('SET_LOADING', true);
                sendReloadModelRequest(parameterValues, clientModelId, internalState.websocket)
                commit('SET_SENT_VALUES', parameterValues)
            }
        },

        sendParameterValue({state, commit}, {parameterName, value}) {
            const websocket = internalState.websocket;
            if (isNull(websocket) || websocket.isClosed(websocket)) {
                return;
            }

            const newStateVersion = state.clientStateVersion + 1
            commit('SET_CLIENT_STATE_VERSION', newStateVersion)

            if (state.sentValues[parameterName] !== value) {
                for (const parameter of state.parameters) {
                    if (parameter.requiredParameters && parameter.requiredParameters.includes(parameterName)) {
                        commit('SET_AWAIT_DEPENDENCY', {
                            parameterName: parameter.name,
                            shouldAwait: true,
                            newStateVersion
                        })
                    }
                }

                commit('SET_SENT_VALUE', {parameterName, value})
                sendParameterValue(parameterName, value, websocket, newStateVersion);
            }
        },

        setConnection({state, dispatch}, websocket) {
            const existingWebsocket = internalState.websocket;

            if (!isNull(existingWebsocket) && !existingWebsocket.isClosed()) {
                existingWebsocket.close();
            }

            internalState.websocket = websocket;
        },

        resendValues({state}) {
            const websocket = internalState.websocket;
            if (isNull(websocket) || websocket.isClosed()) {
                return;
            }

            forEachKeyValue(state.sentValues, (key, value) => sendParameterValue(key, value, websocket));
        },
    },
    mutations: {
        RESET_CONFIG(state) {
            internalState.reconnectionAttempt = 0;

            state.scriptConfig = null;
            state.parameters = [];
            state.loadError = null;
            state.loading = false;
            state.sentValues = {};
        },

        SET_ERROR(state, error) {
            state.loadError = error;
            state.loading = false;
        },

        UPDATE_SCRIPT_CONFIG(state, config) {
            state.scriptConfig = config;

            const newParameters = config.parameters;
            for (const parameter of newParameters) {
                _preprocessParameter(parameter, state.scriptConfig);
            }

            if (isEmptyArray(state.parameters)) {
                state.parameters = newParameters;
                return;
            }

            const oldParametersDict = toDict(state.parameters, 'name');
            const newParametersDict = toDict(newParameters, 'name');

            forEachKeyValue(oldParametersDict, function (name, parameter) {
                if (name in newParametersDict) {
                    return;
                }

                removeElement(state.parameters, parameter);
            });

            forEachKeyValue(newParametersDict, (name, parameter) => {
                if (name in oldParametersDict) {
                    const index = state.parameters.indexOf(oldParametersDict[name]);
                    Vue.set(state.parameters, index, parameter);
                } else {
                    state.parameters.push(parameter);
                }
            });
        },

        ADD_PARAMETER(state, parameter) {
            _preprocessParameter(parameter, state.scriptConfig);
            state.parameters.push(parameter);
        },

        UPDATE_PARAMETER(state, parameter) {
            let foundIndex = -1;

            const parameters = state.parameters;

            for (let i = 0; i < parameters.length; i++) {
                const anotherParam = parameters[i];
                if (anotherParam['name'] === parameter['name']) {
                    foundIndex = i;
                    break;
                }
            }

            if (foundIndex < 0) {
                console.log('Failed to find parameter ' + parameter['name']);
                return;
            }

            const oldParameter = parameters[foundIndex]
            parameter.loading = oldParameter.loading
            parameter.awaitedVersion = oldParameter.awaitedVersion

            _preprocessParameter(parameter, state.scriptConfig);
            Vue.set(parameters, foundIndex, parameter);
        },

        REMOVE_PARAMETER(state, data) {
            const parameterName = data.parameterName
            let foundIndex = -1;

            const parameters = state.parameters;

            for (let i = 0; i < parameters.length; i++) {
                const parameter = parameters[i];

                if (parameter['name'] === parameterName) {
                    foundIndex = i;
                    break;
                }
            }

            if (foundIndex < 0) {
                console.log('Failed to find parameter ' + parameterName);
                return;
            }

            parameters.splice(foundIndex, 1);
        },

        SET_SENT_VALUE(state, {parameterName, value}) {
            state.sentValues[parameterName] = value;
        },

        SET_SENT_VALUES(state, parameterValues) {
            state.sentValues = clone(parameterValues)
        },

        SET_LOADING(state, loading) {
            state.loading = loading;
        },

        SET_CLIENT_STATE_VERSION(state, clientStateVersion) {
            state.clientStateVersion = clientStateVersion;
        },

        SET_AWAIT_DEPENDENCY(state, {parameterName, shouldAwait, newStateVersion}) {
            for (const parameter of state.parameters) {
                if (parameter.name === parameterName) {
                    Vue.set(parameter, 'loading', shouldAwait)
                    parameter.awaitedVersion = newStateVersion
                    break
                }
            }
        },

        RESET_AWAITED_DEPENDENCIES(state, {clientStateVersion}) {
            if (!clientStateVersion) {
                return
            }

            for (const parameter of state.parameters) {
                if ((parameter.awaitedVersion) && (parameter.awaitedVersion <= clientStateVersion)) {
                    Vue.set(parameter, 'loading', false)
                    parameter.awaitedVersion = null
                    break
                }
            }
        }
    }
})

function reconnect(state, internalState, commit, dispatch, selectedScript) {
    let dataReceived = false;

    let initWithValues = false
    if (!isNull(state.scriptConfig) && !isEmptyObject(state.sentValues)) {
        initWithValues = true
    }

    const uri = 'scripts/' + encodeURIComponent(selectedScript) + '?initWithValues=' + initWithValues
    const socket = new ReactiveWebSocket(uri, {
        onNext: function (rawMessage) {
            internalState.reconnectionAttempt = 0;

            dataReceived = true;

            const event = JSON.parse(rawMessage);

            const eventType = event.event;
            const data = event.data;
            const clientStateVersion = event.data.clientStateVersion;

            commit('RESET_AWAITED_DEPENDENCIES', {clientStateVersion})

            if (isNull(state.scriptConfig) && (eventType !== 'initialConfig')) {
                console.error('Expected "initialConfig" event, but got ' + eventType);
                commit('SET_ERROR', 'Unexpected error occurred');
                socket.close();
                return;
            }

            if (eventType === 'initialConfig') {
                commit('UPDATE_SCRIPT_CONFIG', data);
                commit('SET_LOADING', false);
                dispatch('resendValues');
                return;
            }

            if (eventType === 'reloadedConfig') {
                commit('UPDATE_SCRIPT_CONFIG', data);
                commit('SET_LOADING', false);
                return;
            }

            if (eventType === 'parameterChanged') {
                commit('UPDATE_PARAMETER', data);
                return;
            }

            if (eventType === 'parameterAdded') {
                commit('ADD_PARAMETER', data);
                return;
            }

            if (eventType === 'parameterRemoved') {
                commit('REMOVE_PARAMETER', data);
            }
        },

        onError: function (error) {
            logError(error);

            if (error instanceof SocketClosedError) {
              
                if (error.code === 422) {
                  commit('SET_ERROR', `${CANNOT_PARSE_ERROR_PREFIX} "${selectedScript}"`);
                  return;
                }
                
                console.log('Socket closed. code=' + error.code + ', reason=' + error.reason);
              
                if (isNull(state.scriptConfig)) {
                    commit('SET_ERROR', 'Failed to connect to the server');
                    return;
                }

                internalState.reconnectionAttempt++;

                if (internalState.reconnectionAttempt > 5) {
                    commit('SET_ERROR', 'Failed to reconnect');
                    return;
                }

                setTimeout(function () {
                    console.log('Trying to reconnect. Attempt ' + internalState.reconnectionAttempt);
                    reconnect(state, internalState, commit, dispatch, selectedScript);
                }, (internalState.reconnectionAttempt - 1) * reconnectionDelay);

                return;
            }

            if (error instanceof HttpForbiddenError) {
                commit('SET_ERROR', 'Access to the script is denied');
                return;
            }

            if (error instanceof HttpUnauthorizedError) {
                commit('SET_ERROR', 'Failed to authenticate the user');
                return;
            }

            if ((error instanceof HttpRequestError) && (error.code === 404)) {
                commit('SET_ERROR', `${NOT_FOUND_ERROR_PREFIX} "${selectedScript}"`);
                return;
            }

            commit('SET_ERROR', 'Unexpected error occurred');
        },

        onComplete: function () {
            console.log('Websocket completed. This should not be possible for a config socket');
            commit('SET_ERROR', 'Connection to server closed');
        }
    });

    if (initWithValues) {
        socket.send(JSON.stringify({
            'event': 'initialValues',
            data: {
                'parameterValues': state.sentValues
            }
        }))
    }

    dispatch('setConnection', socket);
}

function _preprocessParameter(parameter, scriptConfig) {
    preprocessParameter(parameter, (path) => {
        return loadFiles(scriptConfig, parameter.name, path);
    });
}

function loadFiles(scriptConfig, parameterName, path) {
    if (isNull(scriptConfig)) {
        throw Error('Config is not available');
    }

    const encodedScript = encodeURIComponent(scriptConfig.name);
    const encodedParameter = encodeURIComponent(parameterName);
    const url = `scripts/${encodedScript}/${encodedParameter}/list-files`;
    const param = toQueryArgs({'path': path, 'id': scriptConfig.id});
    const full_url = url + '?' + param;

    return axiosInstance.get(full_url)
        .then(({data}) => data);
}