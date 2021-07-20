import '@/common/materializecss/imports/tabs'
import '@/common/style_imports';
import Vue from 'vue';
import AdminApp from './AdminApp';
import './AdminApp';
import router from './router/router';
import vueDirectives from '@/common/vueDirectives'
import {forEachKeyValue} from '@/common/utils/common'

forEachKeyValue(vueDirectives, (id, definition) => {
    Vue.directive(id, definition)
})

//noinspection JSAnnotator
new Vue({
    router,
    render: h => h(AdminApp)
}).$mount('#admin-page');
