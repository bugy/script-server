import '@/common/style_imports'
import {forEachKeyValue} from '@/common/utils/common';
import Vue from 'vue'
import MainApp from './MainApp.vue';
import router from './router/router'
import store from './store'
import vueDirectives from '@/common/vueDirectives'

Vue.config.productionTip = false;

forEachKeyValue(vueDirectives, (id, definition) => {
    Vue.directive(id, definition)
})

new Vue({
    router,
    store,
    render: h => h(MainApp)
}).$mount('#app');