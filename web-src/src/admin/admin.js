import 'material-design-icons/iconfont/material-icons.css';
import 'typeface-roboto';
import '@/assets/css/shared.css';
import {createApp} from 'vue';
import AdminApp from './AdminApp';
import router from './router/router';
import store from './store/index';
import vueDirectives from '@/common/vueDirectives'
import vuetify from '@/common/vuetifyPlugin'
import {forEachKeyValue} from '@/common/utils/common'

const app = createApp(AdminApp)

forEachKeyValue(vueDirectives, (id, definition) => {
    app.directive(id, definition)
})

app.use(router).use(store).use(vuetify)
app.mount('#admin-page')
