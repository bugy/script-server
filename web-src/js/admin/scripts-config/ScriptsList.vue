<template>
    <div class="collection container scripts-list">
        <PageProgress v-if="loading"/>
        <router-link :key="script" :to="script" append class="collection-item" v-else
                     v-for="script in scripts">
            {{script}}
        </router-link>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import PageProgress from '../components/PageProgress';

    export default {
        name: 'ScriptsList',

        mounted: function () {
            this.init();
        },

        computed: {
            ...mapState('scripts', {
                scripts: 'scripts',
                loading: 'loading'
            })
        },

        components: {
            PageProgress
        },

        methods: {
            ...mapActions('scripts', ['init'])
        }
    }
</script>

<style scoped>
    .scripts-list {
        margin-top: 1.5em;
        margin-bottom: 1em;
    }
</style>