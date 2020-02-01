import Vue from 'vue';
import VueRouter from 'vue-router';
import {routerChildren as executionRouterChildren} from '../history/executions-log-page';
import AppWelcomePanel from './AppWelcomePanel';
import AppHistoryHeader from './history/AppHistoryHeader';
import AppHistoryPanel from './history/AppHistoryPanel';
import MainAppContent from './scripts/MainAppContent';
import ScriptHeader from './scripts/ScriptHeader';

Vue.use(VueRouter);

const router = new VueRouter({
    mode: 'hash',
    routes: [
        {
            path: '/history',
            components: {
                default: AppHistoryPanel,
                header: AppHistoryHeader
            },
            children: executionRouterChildren
        },
        {
            path: '/:scriptName',
            components: {
                default: MainAppContent,
                header: ScriptHeader
            },
            name: 'script'
        },
        {
            path: '',
            component: AppWelcomePanel
        }
    ]
});

export default router