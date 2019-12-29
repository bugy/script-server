import axios from 'axios';
import Vue from 'vue';
import {isEmptyObject, isEmptyString, isNull} from '../../common';
import {scriptNameToHash} from '../model_helper';
import router from '../router';

export default {
    namespaced: true,

    state: {
        scripts: [],
        selectedScript: null,
        predefinedParameters: null
    },

    actions: {
        init({commit, dispatch}) {
            router.afterEach((to, from) => {
                dispatch('selectScriptByHash');
            });

            axios.get('scripts')
                .then(({data: scripts}) => {
                    scripts.sort(function (name1, name2) {
                        return name1.toLowerCase().localeCompare(name2.toLowerCase());
                    });

                    commit('SET_SCRIPTS', scripts);
                    dispatch('selectScriptByHash');
                });
        },

        selectScriptByHash({state, commit}) {
            let encodedScriptName;
            let queryParameters;
            if (router.currentRoute.name === 'script') {
                encodedScriptName = router.currentRoute.params['scriptName'];
                queryParameters = router.currentRoute.query;
            } else {
                queryParameters = null;
                encodedScriptName = null;
            }

            let newSelectedScript = null;

            for (const script of state.scripts) {
                const scriptHash = scriptNameToHash(script);
                if (scriptHash === encodedScriptName) {
                    newSelectedScript = script;
                    break;
                }
            }

            if (!isEmptyString(encodedScriptName) && isNull(newSelectedScript)) {
                newSelectedScript = encodedScriptName;
            }

            if (isEmptyObject(queryParameters)) {
                queryParameters = null;
            }

            commit('SELECT_SCRIPT', {selectedScript: newSelectedScript, predefinedParameters: queryParameters});

            if (!isEmptyObject(queryParameters)) {
                Vue.nextTick(() => router.replace({query: null}));
            }
        }
    },

    mutations: {
        SET_SCRIPTS(state, scripts) {
            state.scripts = scripts
        },

        SELECT_SCRIPT(state, {selectedScript, predefinedParameters}) {
            state.selectedScript = selectedScript;
            state.predefinedParameters = predefinedParameters;
        }
    }
}