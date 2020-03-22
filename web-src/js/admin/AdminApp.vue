<template>
    <div class="admin-page">
        <div class="page-title teal z-depth-1">
            <a class="btn-flat left home-button" href="index.html">
                <i class="material-icons white-text">home</i>
            </a>
            <ul class="tabs tabs-fixed-width" ref="tabs">
                <li class="tab">
                    <router-link to="/logs">Logs</router-link>
                </li>
                <li class="tab">
                    <router-link to="/scripts">Scripts</router-link>
                </li>
            </ul>
            <div class="subheader" v-if="subheader">{{ subheader }}</div>
        </div>
        <router-view class="page-content"/>
    </div>
</template>

<script>
    import Vue from 'vue';
    import Vuex, {mapActions, mapState} from 'vuex';
    import executions from '../history/executions-module';
    import scriptConfig from './scripts-config/script-config-module';
    import scripts from './scripts-config/scripts-module';

    Vue.use(Vuex);

    const store = new Vuex.Store({
        state: {
            subheader: null
        },
        modules: {
            'history': executions(),
            scripts: scripts,
            scriptConfig: scriptConfig
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

    export default {
        name: 'AdminApp',
        store,

        mounted() {
            const instance = M.Tabs.init(this.$refs.tabs, {});
        },

        computed: {
            ...mapState(['subheader'])
        },

        methods: {
            ...mapActions(['setSubheader'])
        },

        watch: {
            $route() {
                this.setSubheader(null);
            }
        }
    }
</script>

<style scoped>
    .admin-page {
        display: flex;
        flex-direction: column;

        background: white;
        font-family: "Roboto", sans-serif;
        font-weight: normal;

        height: 100vh;
    }

    .page-title {
        flex: 0 0 0;
        width: 100%;

        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
    }

    .tabs.tabs-fixed-width {
        max-width: 30em;
        background: none;
    }

    .tabs.tabs-fixed-width .tab a {
        font-size: 1em;
        font-weight: 500;
        letter-spacing: 1px;

        color: rgba(255, 255, 255, 0.7);
    }

    .tabs.tabs-fixed-width .tab a.active {
        color: #FFF;
    }

    .subheader {
        font-size: 1em;
        font-weight: 400;

        text-transform: uppercase;
        text-align: center;
        color: #FFF;

        margin-top: 0.8em;
        margin-bottom: 0.8em;
    }

    .admin-page >>> .tabs.tabs-fixed-width .indicator {
        background-color: white;
    }

    .page-content {
        flex: 1 1 0;
        overflow-y: auto;
    }

    .home-button {
        height: 100%;
        padding-left: 20px;
        padding-right: 20px;
    }

    .home-button i {
        font-size: 1.8em;
        line-height: 1.8em;
    }
</style>