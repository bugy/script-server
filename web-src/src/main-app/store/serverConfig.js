import axios from 'axios';

export default {
    namespaced: true,

    state: {
        serverName: null,
        enableScriptTitles: null,
        version: null
    },

    mutations: {
        SET_CONFIG(state, config) {
            state.serverName = config.title;
            state.version = config.version;
            state.enableScriptTitles = config.enableScriptTitles;
        }
    },

    actions: {
        init({commit}) {
            axios.get('conf').then(({data: config}) => {
                commit('SET_CONFIG', config);
            });
        }
    }
}