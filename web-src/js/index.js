import Vue from 'vue';

import './connections/rxWebsocket.js';
import MainApp from './main-app/MainApp.vue';
import router from './main-app/router';
import store from './main-app/store'
import './style_imports.js';

window.onload = onLoad;

function onLoad() {
    new Vue({
        el: '#index-page',
        store,
        router,
        render: h => h(MainApp)
    });
}
