import axios from 'axios';
import Vue from 'vue'
import Vuex from 'vuex'
import {isNull, logError} from '../../common';
import authModule from './auth';

import scriptConfigModule from './scriptConfig';
import scriptExecutionManagerModule from './scriptExecutionManager';
import scriptsModule from './scripts';
import scriptSetupModule from './scriptSetup';
import serverConfigModule from './serverConfig';


Vue.use(Vuex);

const store = new Vuex.Store({
    modules: {
        scripts: scriptsModule,
        serverConfig: serverConfigModule,
        scriptConfig: scriptConfigModule,
        scriptSetup: scriptSetupModule,
        executions: scriptExecutionManagerModule,
        auth: authModule
    },
    actions: {
        init({dispatch}) {
            dispatch('auth/init');
            dispatch('serverConfig/init');
            dispatch('scripts/init');
            dispatch('executions/init');
        },

        logout({dispatch}) {
            dispatch('executions/stopAll')
                .then(() => dispatch('auth/logout'))
                .then(() => location.reload())
                .catch(e => e && logError(e));
        }
    },
    mutations: {},

    strict: process.env.NODE_ENV !== 'production'
});

store.watch((state) => state.scripts.selectedScript, (selectedScript) => {
    store.dispatch('scriptSetup/reset');
    store.dispatch('scriptConfig/reloadScript', {selectedScript});
    store.dispatch('executions/selectScript', {selectedScript});

    const predefinedParameters = store.state.scripts.predefinedParameters;
    if (!isNull(predefinedParameters)) {
        store.dispatch('scriptSetup/setParameterValues', {
            values: predefinedParameters, forceAllowedValues: false
        });
    }
});

store.watch((state) => state.scriptConfig.parameters, (parameters) => {
    let scriptName = store.state.scriptConfig.scriptConfig ? store.state.scriptConfig.scriptConfig.name : null;
    store.dispatch('scriptSetup/initFromParameters', {scriptName, parameters});
});

axios.interceptors.response.use((response) => response, (error) => {
    if (error.response.status === 401) {
        store.dispatch('auth/setAuthenticated', false);
    }
    throw error;
});

window.addEventListener('beforeunload', function (e) {
    if (store.getters['executions/hasActiveExecutors']) {
        e = e || window.event;

        // in modern browsers the message will be replaced with default one (security reasons)
        var message = 'Closing the page will stop all running scripts. Are you sure?';
        e.returnValue = message;

        return message;
    }
});

export default store;