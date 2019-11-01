import axios from 'axios';
import {contains, forEachKeyValue, isEmptyValue} from '../../common';
import router from '../router'

const allowedEmptyValuesInParam = ['name'];

function removeEmptyValues(config) {
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

export default {
    state: {
        scriptName: null,
        scriptConfig: null,
        scriptFilename: null,
        error: null
    },
    namespaced: true,
    actions: {
        init({commit, state}, scriptName) {
            commit('RESET', scriptName);

            axios.get('admin/scripts/' + scriptName)
                .then(({data}) => {
                    commit('SET_SCRIPT_CONFIG', {config: data.config, filename: data.filename});
                })
                .catch((error) => {
                    commit('SET_LOAD_ERROR', 'Failed to load script config')
                });
        },

        save({dispatch, state}) {
            const config = $.extend({}, state.scriptConfig);
            const oldName = state.scriptName;

            removeEmptyValues(config);

            return axios.put('admin/scripts', {
                config,
                filename: state.scriptFilename
            })
                .then(() => {
                    const newName = config.name;

                    if (oldName === newName) {
                        dispatch('init', newName);
                    } else {
                        router.push({
                            path: `/scripts/${newName}`
                        });
                    }
                });
        }
    },
    mutations: {
        RESET(state, scriptName) {
            state.scriptName = scriptName;
            state.scriptConfig = null;
            state.scriptFilename = null;
            state.error = null;
        },

        SET_SCRIPT_CONFIG(state, {config, filename}) {
            state.error = null;
            state.scriptConfig = config;
            state.scriptFilename = filename;
        },

        SET_LOAD_ERROR(state, error) {
            state.error = error;
            state.scriptConfig = null;
            state.scriptFilename = null;
        }
    }
}