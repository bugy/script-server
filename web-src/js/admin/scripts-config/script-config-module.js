import axios from 'axios';

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

        save({state}) {
            return axios.put('admin/scripts', {
                config: state.scriptConfig,
                filename: state.scriptFilename
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