<template>
    <div>
        <router-view/>
    </div>
</template>

<script>
    import {mapActions, mapState} from 'vuex';
    import PageProgress from '../components/PageProgress';
    import ScriptsList from './ScriptsList';

    export default {
        name: 'ScriptConfigListPage',

        components: {}
    }
</script>

<style scoped>

</style>