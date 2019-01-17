import Vue from 'vue';
import VueRouter from 'vue-router';
import './style_imports';
import ExecutionsLogPage from './admin/executions-log-page';
import ExecutionsLog from './admin/executions-log';
import ExecutionDetails from './admin/execution-details';

Vue.use(VueRouter);

document.addEventListener('DOMContentLoaded', function () {
    var router = new VueRouter({
        mode: 'hash',
        routes: [
            {
                path: '/executions',
                component: ExecutionsLogPage,
                children: [
                    {path: '', component: ExecutionsLog},
                    {path: ':executionId', component: ExecutionDetails}
                ]
            },
            {path: '*', redirect: '/executions'}
        ]
    });

    //noinspection JSAnnotator
    new Vue({
        router,
        el: '#admin-page',
        render(createElement) {
            return createElement('div', {}, [createElement('router-view')]);
        }
    });

}, false);


