<template xmlns:v-slot="http://www.w3.org/1999/XSL/Transform">
    <div id="main-app">
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
    import '@/assets/css/index.css';
    import AppLayout from '@/common/components/AppLayout';
    import {isEmptyString} from '@/common/utils/common';
    import {mapActions} from 'vuex';
    import AppWelcomePanel from './components/AppWelcomePanel';
    import DocumentTitleManager from './components/DocumentTitleManager';
    import FaviconManager from './components/FaviconManager';
    import MainAppSidebar from './components/MainAppSidebar';
    import MainAppContent from './components/scripts/MainAppContent';

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