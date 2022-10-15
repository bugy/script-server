import {isEmptyObject, isEmptyString, isNull} from '@/common/utils/common';
import Vue from 'vue';
import router from '../router/router';
import {scriptNameToHash} from '../utils/model_helper';
import {axiosInstance} from '@/common/utils/axios_utils';

export default {
    namespaced: true,

    state: {
        scripts: [],
        failedScripts: [],
        selectedScript: null,
        predefinedParameters: null
    },

    actions: {
        init({commit, dispatch}) {
            router.afterEach((to, from) => {
                dispatch('selectScriptByHash');
            });

            axiosInstance.get('scripts')
                .then(({data}) => {
                    const {scripts} = data;
                    scripts.sort(function (script1, script2) {
                        return script1.name.toLowerCase().localeCompare(script2.name.toLowerCase());
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
                const scriptHash = scriptNameToHash(script.name);
                if (scriptHash === encodedScriptName) {
                    newSelectedScript = script.name;
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