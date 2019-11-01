import Vue from 'vue';
import AdminApp from './admin/AdminApp';
import router from './admin/router';
import './style_imports';

document.addEventListener('DOMContentLoaded', function () {

    //noinspection JSAnnotator
    new Vue({
        router,
        el: '#admin-page',
        render: h => h(AdminApp)
    });

}, false);


