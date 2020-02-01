<template>
    <div class="main-content-header">
        <router-link :to="baseRoute" class="breadcrumb">
            <h3 class="header">History</h3>
        </router-link>
        <router-link :to="$route.path" class="breadcrumb" v-if="selectedExecutionString">
            <h3 class="header">{{ selectedExecutionString }}</h3>
        </router-link>
    </div>
</template>

<script>
    import {mapState} from 'vuex';
    import {isNull} from '../../common';

    export default {
        name: 'AppHistoryHeader',

        computed: {
            ...mapState('history', ['selectedExecution']),

            baseRoute: function () {
                return this.$route.matched[0].path;
            },

            selectedExecutionString: function () {
                const execution = this.selectedExecution;
                if (isNull(execution)) {
                    return null;
                }

                return '#' + execution.id + ' - ' + execution.user + '@' + execution.script;
            }
        }
    }
</script>

<style scoped>
    .main-content-header {
        padding: 0.9rem;
    }

    .main-content-header h3 {
        display: inline;
        padding: 0 0.3rem;
    }

    .main-content-header h3,
    .main-content-header .breadcrumb:before {
        color: rgba(0, 0, 0, 0.87);
        line-height: 25px;
    }
</style>