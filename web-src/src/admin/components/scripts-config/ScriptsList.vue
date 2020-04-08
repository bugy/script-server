<template>
    <div class="container scripts-list">
        <PageProgress v-if="loading"/>
        <div v-else>
            <router-link :to="newScriptPath" append class="waves-effect waves-light btn add-script-btn">
                <i class="material-icons left">add</i>
                Add
            </router-link>
            <div class="collection">
                <router-link :key="script.name" :to="script.path" append class="collection-item"
                             v-for="script in scripts">
                    {{script.name}}
                </router-link>
            </div>
        </div>
    </div>
</template>

<script>
    import PageProgress from '@/common/components/PageProgress';
    import {mapActions, mapState} from 'vuex';
    import {NEW_SCRIPT} from '../../store/script-config-module';

    export default {
        name: 'ScriptsList',

        mounted: function () {
            this.init();
        },

        data() {
            return {
                newScriptPath: NEW_SCRIPT
            }
        },

        computed: {
            ...mapState('scripts', {
                scripts: state => {
                    return state.scripts ? state.scripts.map(s => ({name: s, path: encodeURIComponent(s)})) : []
                },
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

    .add-script-btn {
        margin-bottom: 1em;
    }
</style>