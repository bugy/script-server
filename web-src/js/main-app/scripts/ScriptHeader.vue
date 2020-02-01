<template>
    <h2 class="script-header header main-content-header" v-show="selectedScript">{{ selectedScript }}</h2>
</template>

<script>
    import {mapState} from 'vuex';

    export default {
        name: 'ScriptHeader',

        computed: {
            ...mapState('scripts', {
                selectedScript: 'selectedScript'
            })
        }
    }
</script>

<style scoped>
</style>