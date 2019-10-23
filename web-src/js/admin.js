import Vue from 'vue';
import VueRouter from 'vue-router';
import AdminApp from './admin/AdminApp';
import ExecutionDetails from './admin/executions/execution-details';
import ExecutionsLog from './admin/executions/executions-log';
import ExecutionsLogPage from './admin/executions/executions-log-page';
import ScriptConfig from './admin/scripts-config/ScriptConfig';
import ScriptConfigListPage from './admin/scripts-config/ScriptConfigListPage';
import './style_imports';
import ScriptsList from './admin/scripts-config/ScriptsList';

Vue.use(VueRouter);

document.addEventListener('DOMContentLoaded', function () {

    const router = new VueRouter({
        mode: 'hash',
        routes: [
            {
                path: '/logs',
                component: ExecutionsLogPage,
                children: [
                    {path: '', component: ExecutionsLog},
                    {path: ':executionId', component: ExecutionDetails}
                ]
            },
            {
                path: '/scripts',
                component: ScriptConfigListPage,
                children: [
                    {path: '', component: ScriptsList},
                    {path: ':scriptName', component: ScriptConfig, props: true}
                ]
            },
            {path: '*', redirect: '/logs'}
        ],
        linkActiveClass: 'active'
    });


    //noinspection JSAnnotator
    new Vue({
        router,
        el: '#admin-page',
        render: h => h(AdminApp)
    });

}, false);


