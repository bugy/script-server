import {forEachKeyValue, guid, isEmptyObject, isEmptyString, isNull, removeElement} from '@/common/utils/common';
import Vue from 'vue';
import clone from 'lodash/clone';
import isEqual from 'lodash/isEqual';

export default {
    namespaced: true,
    state: {
        parameterValues: {},
        forcedValueParameters: [],
        errors: {},
        nextReloadValues: null,
        _parameterAllowedValues: {}
    },
    actions: {
        reset({commit}) {
            commit('SET_ERRORS', {});
            commit('SET_VALUES', {});
            commit('SET_FORCED_VALUE_PARAMETERS', []);
            commit('SET_NEXT_RELOAD_VALUES', null);
        },

        initFromParameters({state, dispatch, commit}, {scriptConfig, parameters}) {
            const oldParameterAllowedValues = state._parameterAllowedValues

            commit('CACHE_PARAMETER_ALLOWED_VALUES', parameters)

            if (!isNull(state.nextReloadValues) && !isNull(scriptConfig)) {
                const forceAllowedValues = state.nextReloadValues.forceAllowedValues
                const parameterValues = state.nextReloadValues.parameterValues
                const expectedReloadedScript = state.nextReloadValues.scriptName
                const expectedReloadedModelId = state.nextReloadValues.clientModelId

                if (expectedReloadedScript !== scriptConfig.name) {
                    commit('SET_NEXT_RELOAD_VALUES', null);
                } else if (expectedReloadedModelId === scriptConfig.clientModelId) {
                    commit('SET_VALUES', parameterValues);
                    commit('SET_NEXT_RELOAD_VALUES', null);
                    commit('SET_FORCED_VALUE_PARAMETERS', forceAllowedValues ? Object.keys(parameterValues) : []);
                    return;
                }
            }

            commit('UPDATE_FORCED_PARAMETERS', {oldParameterAllowedValues})

            if (!isEmptyObject(state.parameterValues)) {
                for (const parameter of parameters) {
                    const parameterName = parameter.name;
                    if (!state.parameterValues.hasOwnProperty(parameterName)) {
                        let value;
                        if (!isNull(parameter.default)) {
                            value = parameter.default;
                        } else {
                            value = null;
                        }

                        dispatch('setParameterValue', {parameterName, value});
                    }
                }

                return;
            }

            const values = {};
            for (const parameter of parameters) {
                if (!isNull(parameter.default)) {
                    values[parameter.name] = parameter.default;
                } else {
                    values[parameter.name] = null;
                }
            }

            dispatch('_setAndSendParameterValues', values);
        },

        setParameterValue({state, commit, dispatch}, {parameterName, value}) {
            commit('UPDATE_SINGLE_VALUE', {parameterName, value});
            dispatch('sendValueToServer', {parameterName, value});
        },

        setParameterError({commit}, {parameterName, errorMessage}) {
            commit('UPDATE_PARAMETER_ERROR', {parameterName, errorMessage})
        },

        reloadModel({state, commit, dispatch}, {values, forceAllowedValues, scriptName}) {
            commit('SET_FORCED_VALUE_PARAMETERS', []);

            if (isEqual(state.parameterValues, values)) {
                return
            }

            const clientModelId = guid(16)

            commit('SET_VALUES', values)
            commit('SET_NEXT_RELOAD_VALUES', {parameterValues: values, forceAllowedValues, scriptName, clientModelId});

            dispatch('scriptConfig/reloadModel', {scriptName, parameterValues: values, clientModelId}, {root: true});
        },

        _setAndSendParameterValues({state, commit, dispatch}, values) {
            commit('SET_VALUES', values);

            forEachKeyValue(values, (parameterName, value) => dispatch('sendValueToServer', {
                parameterName,
                value
            }));
        },

        sendValueToServer({state, commit, dispatch}, {parameterName, value}) {
            const valueToSend = (parameterName in state.errors) ? null : value;
            dispatch('scriptConfig/sendParameterValue', {parameterName, value: valueToSend}, {root: true});
        }
    },
    mutations: {
        SET_VALUES(state, values) {
            state.parameterValues = clone(values)
        },
        SET_FORCED_VALUE_PARAMETERS(state, parameterNames) {
            state.forcedValueParameters = clone(parameterNames)
        },
        SET_ERRORS(state, errors) {
            state.errors = errors;
        },
        UPDATE_SINGLE_VALUE(state, {parameterName, value}) {
            if (state.parameterValues[parameterName] !== value) {
                Vue.set(state.parameterValues, parameterName, value);
                removeElement(state.forcedValueParameters, parameterName)
            }
        },
        UPDATE_PARAMETER_ERROR(state, {parameterName, errorMessage}) {
            if (isEmptyString(errorMessage)) {
                delete state.errors[parameterName];
            } else {
                state.errors[parameterName] = errorMessage;
            }
        },
        SET_NEXT_RELOAD_VALUES(state, nextReloadValues) {
            state.nextReloadValues = nextReloadValues;
        },
        CACHE_PARAMETER_ALLOWED_VALUES(state, parameters) {
            state._parameterAllowedValues = parameters
                .filter(p => !isNull(p.values))
                .reduce((result, param) => {
                    result[param.name] = param.values
                    return result
                }, {})
        },
        UPDATE_FORCED_PARAMETERS(state, {oldParameterAllowedValues}) {
            const newParameterAllowedValues = state._parameterAllowedValues

            for (const forcedParameter of clone(state.forcedValueParameters)) {
                const oldValues = oldParameterAllowedValues[forcedParameter]
                const newValues = newParameterAllowedValues[forcedParameter]

                if (isNull(oldValues) || isNull(newValues) || !isEqual(oldValues, newValues)) {
                    removeElement(state.forcedValueParameters, forcedParameter)
                }
            }
        }
    }
}