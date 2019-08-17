<template>
    <div class="main-app-sidebar">
        <div class="list-header">
            <h3 :title="versionString" class="header server-header">Script server</h3>

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

        <div class="logout-panel" v-if="authEnabled">
            <span>{{username}}</span>
            <input :src="logoutIcon" @click="logout" class="logout-button" type="image">
        </div>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import ScriptsList from './ScriptsList'
    import SearchPanel from './SearchPanel';
    import LogoutButton from '../../images/logout.png'

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

    .logout-panel {
        height: 45px;
        width: 100%;
        border-top: 1px solid #C8C8C8;

        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;

        flex-shrink: 0;
    }

    .logout-button {
        margin-left: 10px;
    }

</style>