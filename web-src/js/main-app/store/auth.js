import axios from 'axios';

export default {
    state: {
        enabled: false,
        authenticated: true,
        admin: false,
        username: null
    },
    namespaced: true,
    actions: {
        init({commit}) {
            axios.get('auth/info').then(({data}) => {
                const {username, admin, enabled} = data;

                commit('SET_CONFIG', {username, admin, enabled})
            });
        },

        setAuthenticated({commit}, authenticated) {
            commit('SET_AUTHENTICATED', authenticated);
        },

        logout({}) {
            return axios.post('logout')
                .catch(error => {
                    const {status} = error.response;
                    if (status !== 405) {
                        throw error;
                    }
                });
        }
    },
    mutations: {
        SET_CONFIG(state, {username, admin, enabled}) {
            state.admin = admin;
            state.enabled = enabled;
            state.username = username;
        },

        SET_AUTHENTICATED(state, authenticated) {
            state.authenticated = authenticated;
        }
    }
}