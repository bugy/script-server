import axios from 'axios';
import {getUnparameterizedUrl, isEmptyObject, readQueryParameters} from '../../common';
import {scriptNameToHash} from '../model_helper';

export default {
    namespaced: true,

    state: {
        scripts: [],
        selectedScript: null,
        predefinedParameters: null
    },

    actions: {
        init({commit, dispatch}) {
            window.addEventListener('hashchange', () => {
                dispatch('selectScriptByHash')
            });

            axios.get('scripts')
                .then(({data: scripts}) => {
                    scripts.sort(function (name1, name2) {
                        return name1.toLowerCase().localeCompare(name2.toLowerCase());
                    });

                    commit('SET_SCRIPTS', scripts);
                    dispatch('selectScriptByHash')
                });
        },

        selectScript({commit}, scriptName) {
            commit('SELECT_SCRIPT', scriptName)
        },

        selectScriptByHash({state, commit}) {
            let hash = window.location.href;
            const index = hash.indexOf('#');
            if (index >= 0) {
                hash = decodeURIComponent(hash.slice(index + 1));
            }

            for (const script of state.scripts) {
                const scriptHash = scriptNameToHash(script);
                if (scriptHash === hash) {
                    commit('SELECT_SCRIPT', script);
                    break;
                }
            }

            let queryParameters = readQueryParameters();
            if (isEmptyObject(queryParameters)) {
                queryParameters = null;
            } else {
                history.pushState('', '', getUnparameterizedUrl() + window.location.hash)
            }

            commit('SET_PREDEFINED_PARAMETERS', queryParameters);
        }
    },

    mutations: {
        SET_SCRIPTS(state, scripts) {
            state.scripts = scripts
        },

        SELECT_SCRIPT(state, selectedScript) {
            state.selectedScript = selectedScript
        },

        SET_PREDEFINED_PARAMETERS(state, predefinedParameters) {
            state.predefinedParameters = predefinedParameters;
        }
    }
}