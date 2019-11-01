import Vue from 'vue';
import VueRouter from 'vue-router';
import ExecutionDetails from './executions/execution-details';
import ExecutionsLog from './executions/executions-log';
import ExecutionsLogPage from './executions/executions-log-page';
import ScriptConfig from './scripts-config/ScriptConfig';
import ScriptConfigListPage from './scripts-config/ScriptConfigListPage';
import ScriptsList from './scripts-config/ScriptsList';

Vue.use(VueRouter);

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

export default router