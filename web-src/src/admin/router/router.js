import Vue from 'vue';
import VueRouter from 'vue-router';
import {routerChildren as executionRouterChildren} from '../history/executions-log-page';
import AdminExecutionsLogPage from './history/AdminExecutionsLogPage';
import ScriptConfig from './scripts-config/ScriptConfig';
import ScriptConfigListPage from './scripts-config/ScriptConfigListPage';
import ScriptsList from './scripts-config/ScriptsList';

Vue.use(VueRouter);

const router = new VueRouter({
    mode: 'hash',
    routes: [
        {
            path: '/logs',
            component: AdminExecutionsLogPage,
            children: executionRouterChildren
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