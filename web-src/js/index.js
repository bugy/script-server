import Vue from 'vue';

import './connections/rxWebsocket.js';
import MainApp from './main-app/MainApp.vue';
import store from './main-app/store'
import './style_imports.js';

window.onload = onLoad;

function onLoad() {
    new Vue({
        el: '#index-page',
        store,
        render: h => h(MainApp)
    });
}
