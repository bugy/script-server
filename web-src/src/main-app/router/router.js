import {routerChildren as executionRouterChildren} from '@/common/components/history/executions-log-page';
import {createRouter, createWebHashHistory} from 'vue-router';
import AppWelcomePanel from '../components/AppWelcomePanel';
import AppHistoryHeader from '../components/history/AppHistoryHeader';
import AppHistoryPanel from '../components/history/AppHistoryPanel';
import MainAppContent from '../components/scripts/MainAppContent';
import ScriptHeader from '../components/scripts/ScriptHeader';

const router = createRouter({
    history: createWebHashHistory(),
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
