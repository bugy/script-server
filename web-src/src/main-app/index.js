import 'material-design-icons/iconfont/material-icons.css';
import 'typeface-roboto';
import '@/assets/css/shared.css';
import {isNull} from '@/common/utils/common';
import {axiosInstance} from '@/common/utils/axios_utils';
import get from 'lodash/get';
import {createApp, watch} from 'vue'
import {createPinia} from 'pinia'
import MainApp from './MainApp.vue';
import router from './router/router'
import vueDirectives from '@/common/vueDirectives'
import vuetify from '@/common/vuetifyPlugin'
import {forEachKeyValue} from '@/common/utils/common';
import {useAuthStore} from '@/common/stores/auth';
import {useScriptsStore} from '@/main-app/stores/scripts';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';
import {useScriptSetupStore} from '@/main-app/stores/scriptSetup';
import {useExecutionsStore} from '@/main-app/stores/executions';

const pinia = createPinia()
const app = createApp(MainApp)

forEachKeyValue(vueDirectives, (id, definition) => {
    app.directive(id, definition)
})

app.use(pinia)
app.use(router)
app.use(vuetify)

const scriptsStore = useScriptsStore()
const scriptConfigStore = useScriptConfigStore()
const scriptSetupStore = useScriptSetupStore()

watch(() => scriptsStore.selectedScript, (selectedScript) => {
    scriptSetupStore.reset()
    useScriptConfigStore().reloadScript(selectedScript)
    useExecutionsStore().selectScript({selectedScript})
})

watch(() => scriptsStore.predefinedParameters, (predefinedParameters) => {
    if (!isNull(predefinedParameters)) {
        scriptSetupStore.reloadModel({
            values: predefinedParameters,
            forceAllowedValues: false,
            scriptName: scriptsStore.selectedScript
        })
    }
})

watch(() => scriptConfigStore.parameters, (parameters) => {
    const scriptConfig = scriptConfigStore.scriptConfig
    const scriptName = scriptConfig ? scriptConfig.name : null
    scriptSetupStore.initFromParameters({scriptName, parameters, scriptConfig})
})

axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        if (get(error, 'response.status') === 401) {
            useAuthStore().setAuthenticated(false)
        }
        throw error
    }
)

app.mount('#app')
