<template xmlns:v-slot="http://www.w3.org/1999/XSL/Transform">
    <div>
        <AppLayout>
            <template v-slot:sidebar>
                <MainAppSidebar/>
            </template>
            <template v-slot:header>
                <h2 class="script-header header" v-show="selectedScript">{{ selectedScript }}</h2>
            </template>
            <template v-slot:content>
                <MainAppContent v-if="selectedScript"></MainAppContent>
                <AppWelcomePanel v-else/>
            </template>
        </AppLayout>
        <DocumentTitleManager/>
        <FaviconManager/>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import AppLayout from '../components/AppLayout';
    import AppWelcomePanel from './AppWelcomePanel';
    import DocumentTitleManager from './DocumentTitleManager';
    import FaviconManager from './FaviconManager';
    import MainAppContent from './MainAppContent';
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

        computed: {
            ...mapState('scripts', {
                selectedScript: 'selectedScript'
            })
        },

        created() {
            this.init();
        }
    }
</script>

<style scoped>
    .script-header {
        background: url('../../images/titleBackground.jpg') no-repeat center;
        background-size: cover;
    }
</style>