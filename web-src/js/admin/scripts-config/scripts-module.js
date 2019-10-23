import axios from 'axios';
import {isNull} from '../../common';

export default {
    state: {
        scripts: [],
        loading: false
    },
    namespaced: true,
    actions: {
        init({commit}) {
            commit('SET_LOADING', true);

            axios.get('scripts').then(({data: scripts}) => {
                scripts.sort(function (name1, name2) {
                    return name1.toLowerCase().localeCompare(name2.toLowerCase());
                });

                commit('SET_SCRIPTS', scripts);
                commit('SET_LOADING', false);
            });
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