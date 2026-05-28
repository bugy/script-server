import '@/common/materializecss/imports/tabs'
import '@/common/style_imports';
import {createApp} from 'vue';
import AdminApp from './AdminApp';
import router from './router/router';
import vueDirectives from '@/common/vueDirectives'
import {forEachKeyValue} from '@/common/utils/common'

const app = createApp(AdminApp)

forEachKeyValue(vueDirectives, (id, definition) => {
    app.directive(id, definition)
})

app.use(router)
app.mount('#admin-page')
