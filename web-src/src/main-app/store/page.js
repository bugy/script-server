export default {
    namespaced: true,

    state: {
        pageLoading: false
    },

    actions: {
        setLoading({commit}, loading) {
            commit('SET_LOADING', loading);
        }
    },

    mutations: {
        SET_LOADING(state, loading) {
            state.pageLoading = loading;
        }
    }

}