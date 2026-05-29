import {createStore} from 'vuex';
import executions from '@/common/store/executions-module';
import scriptConfig from './script-config-module';
import scripts from './scripts-module';
import authModule from '@/common/store/auth';

const store = createStore({
    state: {
        subheader: null
    },
    modules: {
        'history': executions(),
        scripts: scripts,
        scriptConfig: scriptConfig,
        auth: authModule
    },
    actions: {
        setSubheader({commit}, subheader) {
            commit('SET_SUBHEADER', subheader);
        }
    },
    mutations: {
        SET_SUBHEADER(state, subheader) {
            if (subheader) {
                state.subheader = subheader;
            } else {
                state.subheader = null;
            }
        }
    }
});

export default store;
