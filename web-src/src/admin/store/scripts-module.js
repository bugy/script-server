import {axiosInstance} from '@/common/utils/axios_utils';

export default {
    state: {
        scripts: [],
        loading: false
    },
    namespaced: true,
    actions: {
        init({commit}) {
            commit('SET_LOADING', true);

            axiosInstance.get('scripts', {params: {mode: 'edit'}}).then(({data}) => {
                const {scripts} = data;
                let scriptNames = scripts.map(s => ({ name: s.name, parsingFailed: s.parsing_failed }));
                scriptNames.sort(function (e1, e2) {
                    return e1.name.toLowerCase().localeCompare(e2.name.toLowerCase());
                });

                commit('SET_SCRIPTS', scriptNames);
                commit('SET_LOADING', false);
            })
        }
    },
    mutations: {
        SET_LOADING(state, loading) {
            state.loading = loading;
        },

        SET_SCRIPTS(state, scripts) {
            state.scripts = scripts;
        }
    }
}