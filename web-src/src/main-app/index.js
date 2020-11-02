import '@/common/style_imports'
import {trimTextNodes} from '@/common/utils/common';
import Vue from 'vue'
import MainApp from './MainApp.vue';
import router from './router/router'
import store from './store'

Vue.config.productionTip = false;

Vue.directive('trim-text', {
    inserted: trimTextNodes,
    componentUpdated: trimTextNodes
})

new Vue({
    router,
    store,
    render: h => h(MainApp)
}).$mount('#app');