<template>
    <div class="executions-log page">
        <div class="page-title teal">
            <router-link :to="baseRoute" class="breadcrumb">Executions</router-link>
            <router-link v-if="selectedExecutionString" :to="$route.path" class="breadcrumb">
                {{ selectedExecutionString }}
            </router-link>
        </div>
        <div class="section">
            <router-view></router-view>
        </div>
    </div>
</template>

<script>
    import Vue from 'vue';
    import Vuex from 'vuex';
    import {isNull} from '../common';
    import ExecutionDetails from './execution-details';
    import ExecutionsLog from './executions-log';

    Vue.use(Vuex);

    const store = new Vuex.Store({
        state: {
            selectedExecution: null
        },
        mutations: {
            selectExecution(state, execution) {
                state.selectedExecution = execution;
            }
        }
    });


    export default {
        name: 'executions-log-page',
        store,

        beforeRouteUpdate(to, from, next) {
            next();
            this.routeChanged(to);
        },

        beforeRouteEnter(to, from, next) {
            next(function (self) {
                self.routeChanged(to);
            });
        },

        methods: {
            routeChanged: function (newRoute) {
                if (isNull(newRoute.params.executionId)) {
                    store.commit('selectExecution', null);
                } else if (isNull(store.state.selectedExecution)) {
                    store.commit('selectExecution', {
                        id: newRoute.params.executionId,
                        user: 'unknown',
                        script: 'unknown'
                    });
                }
            }
        },

        computed: {
            baseRoute: function () {
                return this.$route.matched[0].path;
            },
            selectedExecutionString: function () {
                var execution = this.$store.state.selectedExecution;
                if (isNull(execution)) {
                    return null;
                }

                return '#' + execution.id + ' - ' + execution.user + '@' + execution.script;
            }
        }
    }

    export const childRoutes = [
        {path: '', component: ExecutionsLog},
        {path: ':executionId', component: ExecutionDetails}
    ];

    export {childRoutes as childRoutes2};
</script>
