<template>
    <div class="main-content-header">
        <router-link :to="baseRoute" class="breadcrumb">
            <h3 class="header">History</h3>
        </router-link>
        <router-link :to="$route.path" class="breadcrumb execution-breadcrumb" v-if="selectedExecutionString">
            <h3 class="header">{{ selectedExecutionString }}</h3>
        </router-link>
    </div>
</template>

<script>
    import {isNull} from '@/common/utils/common';
    import {mapState} from 'vuex';

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
        padding: 0;
        height: 56px;
        display: flex;
        align-items: center;
    }

    .main-content-header h3 {
        padding: 0;
        display: inline;
    }

    .main-content-header h3,
    .main-content-header .breadcrumb:before {
        color: rgba(0, 0, 0, 0.87);
        line-height: 1.3em;
        font-size: 1.3em;
    }

    .main-content-header .execution-breadcrumb {
        color: rgba(0, 0, 0, 0.87);
        flex: 1 1 0;
        min-width: 0;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
</style>