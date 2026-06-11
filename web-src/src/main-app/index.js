import '@/common/style_imports'
import {forEachKeyValue} from '@/common/utils/common';
import {createApp} from 'vue'
import MainApp from './MainApp.vue';
import router from './router/router'
import store from './store'
import vueDirectives from '@/common/vueDirectives'
import vuetify from '@/common/vuetifyPlugin'

const app = createApp(MainApp)

forEachKeyValue(vueDirectives, (id, definition) => {
    app.directive(id, definition)
})

app.use(router)
app.use(store)
app.use(vuetify)
app.mount('#app')
