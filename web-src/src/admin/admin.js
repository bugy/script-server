import '@/common/materializecss/imports/tabs'
import '@/common/style_imports';
import Vue from 'vue';
import AdminApp from './AdminApp';
import './AdminApp';
import router from './router/router';


//noinspection JSAnnotator
new Vue({
    router,
    render: h => h(AdminApp)
}).$mount('#admin-page');
