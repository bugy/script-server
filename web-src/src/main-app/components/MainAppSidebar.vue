<template>
    <div class="main-app-sidebar">
        <div class="list-header">
            <router-link :title="versionString" class="header server-header" to="/">
                Script server
            </router-link>

            <SearchPanel v-model="searchText"/>

            <div class="header-link">
                <a class="teal-text" href="admin.html" v-if="adminUser">
                    <i class="material-icons">settings</i>
                </a>
                <a href="https://github.com/bugy/script-server" target="_blank" v-else>
                    <img src="../../images/github.png">
                </a>
            </div>
        </div>

        <ScriptsList :search-text="searchText"/>

        <router-link class="waves-effect waves-teal btn-flat bottom-panel teal-text history-button" to='/history'>
            History
        </router-link>

        <div class="logout-panel bottom-panel" v-if="authEnabled">
            <span>{{username}}</span>
            <input :src="logoutIcon" @click="logout" class="logout-button" type="image">
        </div>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import LogoutButton from '../../images/logout.png'
    import ScriptsList from './scripts/ScriptsList'
    import SearchPanel from './SearchPanel';

    export default {
        name: 'MainAppSidebar',
        components: {
            SearchPanel,
            ScriptsList
        },

        data() {
            return {
                searchText: '',
                logoutIcon: LogoutButton
            }
        },

        computed: {
            ...mapState('serverConfig', {
                versionString: state => state.version ? 'v' + state.version : null
            }),
            ...mapState('auth', {
                adminUser: 'admin',
                username: 'username',
                authEnabled: 'enabled'
            })
        },

        methods: {
            ...mapActions(['logout'])
        }
    }
</script>

<style scoped>
    .list-header {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: flex-end;

        border-bottom: 5px solid transparent; /* This is to make the header on the same level as the script header */

        flex-shrink: 0;

        position: relative;
    }

    .server-header {
        flex-grow: 1;
        margin-left: 0.4rem;

        font-size: 1.64rem;
        padding: 0.8rem;
        font-weight: 300;
        line-height: 110%;
        color: rgba(0, 0, 0, 0.87)
    }

    .main-app-sidebar {
        height: 100%;

        background: white;

        display: flex;
        flex-direction: column;
    }

    .header-link {
        margin: 0 1rem;
        display: flex;
        line-height: 0;
    }

    .history-button {
        line-height: 3em;
        text-align: center;
    }

    .bottom-panel {
        height: 3em;
        width: 100%;
        border-top: 1px solid #C8C8C8;

        flex-shrink: 0;
    }

    .logout-panel {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
    }

    .logout-button {
        margin-left: 10px;
    }

</style>