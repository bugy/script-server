import {routerChildren as executionRouterChildren} from '@/common/components/history/executions-log-page';
import {createRouter, createWebHashHistory} from 'vue-router';
import AdminExecutionsLogPage from '../components/history/AdminExecutionsLogPage';
import ScriptConfig from '../components/scripts-config/ScriptConfig';
import ScriptConfigListPage from '../components/scripts-config/ScriptConfigListPage';
import ScriptsList from '../components/scripts-config/ScriptsList';

const router = createRouter({
    history: createWebHashHistory(),
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
        // Vue Router 4: wildcard must use :pathMatch(.*)* syntax
        {path: '/:pathMatch(.*)*', redirect: '/logs'}
    ],
    linkActiveClass: 'active'
});

export default router
