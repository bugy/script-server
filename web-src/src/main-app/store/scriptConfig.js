import {ReactiveWebSocket} from '@/common/connections/rxWebsocket';
import {
    arraysEqual,
    contains,
    forEachKeyValue,
    HttpForbiddenError,
    HttpRequestError,
    HttpUnauthorizedError,
    isEmptyArray,
    isEmptyString,
    isNull,
    logError,
    removeElement,
    SocketClosedError,
    toDict
} from '@/common/utils/common';
import axios from 'axios';
import Vue from 'vue';
import {toQueryArgs} from '../../common/utils/common';
import {isComboboxParameter, preprocessParameter} from '../utils/model_helper';

const internalState = {
    websocket: null,
    reconnectionAttempt: 0
};

const reconnectionDelay = 500;

function sendParameterValue(parameterName, value, websocket) {
    const data = {parameter: parameterName, value};
    websocket.send(JSON.stringify({
        'event': 'parameterValue',
        data
    }));
}

export const NOT_FOUND_ERROR_PREFIX = `Failed to find the script`;

export default {
    state: {
        scriptConfig: null,
        loadError: null,
        parameters: [],
        sentValues: {},
        forcedAllowedValues: {},
        loading: false
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

        sendParameterValue({state, commit}, {parameterName, value}) {
            const websocket = internalState.websocket;
            if (isNull(websocket) || !websocket.isOpen(websocket)) {
                return;
            }

            if (state.sentValues[parameterName] !== value) {
                commit('SET_SENT_VALUE', {parameterName, value});

                sendParameterValue(parameterName, value, websocket);
            }
        },

        setConnection({state, dispatch}, websocket) {
            const existingWebsocket = internalState.websocket;

            if (!isNull(existingWebsocket) && !existingWebsocket.isClosed()) {
                existingWebsocket.close();
            }

            internalState.websocket = websocket;
        },

        resendValues({state, dispatch}) {
            const websocket = internalState.websocket;
            if (isNull(websocket) || websocket.isClosed()) {
                return;
            }

            forEachKeyValue(state.sentValues, (key, value) => sendParameterValue(key, value, websocket));
        },

        setForcedAllowedValues({state, commit}, values) {
            commit('SET_FORCED_ALLOWED_VALUES', values);

            for (const parameter of state.parameters) {
                if (isComboboxParameter(parameter)) {
                    const forcedValue = values[parameter.name];

                    if (!isNull(forcedValue)) {
                        const newValues = enrichAllowedValues(forcedValue, parameter.values);
                        if (!arraysEqual(newValues, parameter.values)) {
                            commit('SET_PARAMETER_ALLOWED_VALUES', {
                                parameterName: parameter.name,
                                allowedValues: newValues
                            })
                        }
                    }
                }
            }
        }
    },
    mutations: {
        RESET_CONFIG(state) {
            internalState.reconnectionAttempt = 0;

            state.scriptConfig = null;
            state.parameters = [];
            state.loadError = null;
            state.loading = false;
            state.sentValues = {};
            state.forcedAllowedValues = {};
        },

        SET_ERROR(state, error) {
            state.loadError = error;
            state.loading = false;
        },

        UPDATE_SCRIPT_CONFIG(state, config) {
            state.scriptConfig = config;

            const newParameters = config.parameters;
            for (const parameter of newParameters) {
                _preprocessParameter(parameter, state.forcedAllowedValues[parameter.name], state.scriptConfig);
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
            _preprocessParameter(parameter, state.forcedAllowedValues[parameter.name], state.scriptConfig);
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

            _preprocessParameter(parameter, state.forcedAllowedValues[parameter.name], state.scriptConfig);
            Vue.set(parameters, foundIndex, parameter);
        },

        REMOVE_PARAMETER(state, parameterName) {
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

        SET_FORCED_ALLOWED_VALUES(state, values) {
            state.forcedAllowedValues = values;
        },

        SET_PARAMETER_ALLOWED_VALUES(state, {parameterName, allowedValues}) {
            state.parameters.forEach(p => {
                if (p.name === parameterName) {
                    p.values = allowedValues;
                }
            })
        },

        SET_LOADING(state, loading) {
            state.loading = loading;
        }
    }
}

function reconnect(state, internalState, commit, dispatch, selectedScript) {
    let dataReceived = false;

    const socket = new ReactiveWebSocket('scripts/' + encodeURIComponent(selectedScript), {
        onNext: function (rawMessage) {
            internalState.reconnectionAttempt = 0;

            dataReceived = true;

            const event = JSON.parse(rawMessage);

            const eventType = event.event;
            const data = event.data;

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

    dispatch('setConnection', socket);
}

function _preprocessParameter(parameter, forcedAllowedValue, scriptConfig) {
    preprocessParameter(parameter, (path) => {
        return loadFiles(scriptConfig, parameter.name, path);
    });

    if (isComboboxParameter(parameter) && !isNull(forcedAllowedValue)) {
        parameter.values = enrichAllowedValues(forcedAllowedValue, parameter.values);
    }
}

function enrichAllowedValues(value, parameterValues) {
    let newValues = isNull(parameterValues) ? [] : parameterValues.slice();

    if (Array.isArray(value)) {
        for (let j = 0; j < value.length; j++) {
            const valueElement = value[j];
            if (!contains(parameterValues, valueElement)) {
                newValues.push(valueElement);
            }
        }
    } else {
        if (isEmptyArray(parameterValues) || !contains(parameterValues, value)) {
            newValues.push(value);
        }
    }

    return newValues;
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

    return axios.get(full_url)
        .then(({data}) => data);
}