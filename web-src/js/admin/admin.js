import '../style_imports';

import Vue from 'vue';
import VueRouter from 'vue-router';
import {executionsLogPage} from './executions-log';

Vue.use(VueRouter);

document.addEventListener('DOMContentLoaded', function () {
    var router = new VueRouter({
        mode: 'hash',
        routes: [
            {
                path: '/executions',
                component: executionsLogPage,
                children: executionsLogPage.childRoutes
            },
            {path: '*', redirect: '/executions'}
        ]
    });

    //noinspection JSAnnotator
    new Vue({
        router,
        el: '#admin-page',
        template: `
            <div>
                <router-view></router-view>
            </div>`
    });

}, false);


