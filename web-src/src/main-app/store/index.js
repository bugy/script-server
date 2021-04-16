import historyModule from '@/common/store/executions-module';
import {isNull, logError} from '@/common/utils/common';
import get from 'lodash/get';
import Vue from 'vue'
import Vuex from 'vuex'
import authModule from './auth';
import scheduleModule from './scriptSchedule';
import pageModule from './page';

import scriptConfigModule from './scriptConfig';
import scriptExecutionManagerModule from './scriptExecutionManager';
import scriptsModule from './scripts';
import scriptSetupModule from './scriptSetup';
import serverConfigModule from './serverConfig';
import {axiosInstance} from '@/common/utils/axios_utils';


Vue.use(Vuex);

const store = new Vuex.Store({
    modules: {
        scripts: scriptsModule,
        serverConfig: serverConfigModule,
        scriptConfig: scriptConfigModule(),
        scriptSetup: scriptSetupModule,
        executions: scriptExecutionManagerModule,
        auth: authModule,
        history: historyModule(),
        page: pageModule,
        scriptSchedule: scheduleModule
    },
    actions: {
        init({dispatch}) {
            dispatch('auth/init');
            dispatch('serverConfig/init');
            dispatch('scripts/init');
            dispatch('executions/init');
        },

        resetScript({dispatch, state}) {
            const selectedScript = state.scripts.selectedScript

            dispatch('scriptSetup/reset');
            dispatch('scriptConfig/reloadScript', {selectedScript});
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
    store.dispatch('resetScript');
    store.dispatch('executions/selectScript', {selectedScript});
});

store.watch((state) => state.scripts.predefinedParameters, (predefinedParameters) => {
    if (!isNull(predefinedParameters)) {
        store.dispatch('scriptSetup/reloadModel', {
            values: predefinedParameters,
            forceAllowedValues: false,
            scriptName: store.state.scripts.selectedScript
        });
    }
});

store.watch((state) => state.scriptConfig.parameters, (parameters) => {
    const scriptConfig = store.state.scriptConfig.scriptConfig
    const scriptName = scriptConfig ? scriptConfig.name : null;
    store.dispatch('scriptSetup/initFromParameters', {scriptName, parameters, scriptConfig});
});

axiosInstance.interceptors.response.use((response) => response, (error) => {
    if (get(error, 'response.status') === 401) {
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