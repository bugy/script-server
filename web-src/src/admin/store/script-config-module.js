import {contains, forEachKeyValue, isEmptyArray, isEmptyValue} from '@/common/utils/common';
import clone from 'lodash/clone';
import router from '../router/router'
import {axiosInstance} from '@/common/utils/axios_utils';

const allowedEmptyValuesInParam = ['name'];

function removeEmptyValues(config) {
    if (isEmptyArray(config.parameters)) {
        return;
    }

    for (const parameter of config.parameters) {
        let emptyValueKeys = [];
        forEachKeyValue(parameter, (key, value) => {
            if (contains(allowedEmptyValuesInParam, key)) {
                return;
            }

            if (isEmptyValue(value)) {
                emptyValueKeys.push(key);
            }
        });

        emptyValueKeys.forEach(key => delete parameter[key]);
    }
}

export const NEW_SCRIPT = '_new';

export default {
    state: {
        scriptName: null,
        scriptConfig: null,
        scriptFilename: null,
        error: null,
        new: false
    },
    namespaced: true,
    actions: {
        init({commit, state}, scriptName) {
            if (scriptName === NEW_SCRIPT) {
                commit('INIT_NEW_SCRIPT');
                return;
            }

            commit('RESET', scriptName);

            axiosInstance.get('admin/scripts/' + encodeURIComponent(scriptName))
                .then(({data}) => {
                    commit('SET_SCRIPT_CONFIG', {config: data.config, filename: data.filename});
                })
                .catch((error) => {
                    commit('SET_LOAD_ERROR', 'Failed to load script config')
                });
        },

        save({dispatch, state}) {
            const config = clone(state.scriptConfig);
            const oldName = state.scriptName;

            removeEmptyValues(config);

            const axiosAction = state.new ? axiosInstance.post : axiosInstance.put;

            return axiosAction('admin/scripts', {
                config,
                filename: state.scriptFilename
            })
                .then(() => {
                    const newName = config.name;

                    if (oldName === newName) {
                        dispatch('init', newName);
                    } else {
                        router.push({
                            path: `/scripts/${encodeURIComponent(newName)}`
                        });
                    }
                })
                .catch(e => {
                    if (e.response.status === 422) {
                        e.userMessage = e.response.data;
                    }
                    throw e;
                });
        }
    },
    mutations: {
        RESET(state, scriptName) {
            state.scriptName = scriptName;
            state.scriptConfig = null;
            state.scriptFilename = null;
            state.error = null;
            state.new = false;
        },

        SET_SCRIPT_CONFIG(state, {config, filename}) {
            state.error = null;
            state.scriptConfig = config;
            state.scriptFilename = filename;
            state.new = false;
        },

        SET_LOAD_ERROR(state, error) {
            state.error = error;
            state.scriptConfig = null;
            state.scriptFilename = null;
        },

        INIT_NEW_SCRIPT(state) {
            state.scriptName = null;
            state.scriptConfig = {parameters: []};
            state.new = true;
            state.scriptFilename = null;
            state.error = null;
        }
    }
}