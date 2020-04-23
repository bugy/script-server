import '@/common/style_imports'
import Vue from 'vue'
import MainApp from './MainApp.vue';
import router from './router/router'
import store from './store'

Vue.config.productionTip = false;

new Vue({
    router,
    store,
    render: h => h(MainApp)
}).$mount('#app');