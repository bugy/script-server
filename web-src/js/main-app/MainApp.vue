<template xmlns:v-slot="http://www.w3.org/1999/XSL/Transform">
    <div>
        <AppLayout ref="appLayout">
            <template v-slot:sidebar>
                <MainAppSidebar/>
            </template>
            <template v-slot:header>
                <router-view name="header"/>
            </template>
            <template v-slot:content>
                <router-view/>
            </template>
        </AppLayout>
        <DocumentTitleManager/>
        <FaviconManager/>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import {isEmptyString} from '../common';
    import AppLayout from '../components/AppLayout';
    import AppWelcomePanel from './AppWelcomePanel';
    import DocumentTitleManager from './DocumentTitleManager';
    import FaviconManager from './FaviconManager';
    import MainAppContent from './scripts/MainAppContent';
    import MainAppSidebar from './MainAppSidebar';

    export default {
        name: 'App',
        components: {
            AppLayout,
            MainAppSidebar,
            MainAppContent,
            AppWelcomePanel,
            DocumentTitleManager,
            FaviconManager
        },
        methods: {
            ...mapActions({
                init: 'init'
            })
        },

        created() {
            this.init();
        },

        mounted() {
            const currentPath = this.$router.currentRoute.path;
            this.$refs.appLayout.setSidebarVisibility(isEmptyString(currentPath) || (currentPath === '/'));

            this.$router.afterEach((to) => {
                this.$refs.appLayout.setSidebarVisibility(false);
            });
        }
    }
</script>

<style scoped>
</style>