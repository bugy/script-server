import {defineStore} from 'pinia'
import {axiosInstance} from '@/common/utils/axios_utils'

export const useServerConfigStore = defineStore('serverConfig', {
    state: () => ({
        serverName: null,
        enableScriptTitles: null,
        version: null
    }),
    actions: {
        init() {
            axiosInstance.get('conf').then(({data: config}) => {
                this.serverName = config.title
                this.version = config.version
                this.enableScriptTitles = config.enableScriptTitles
            })
        }
    }
})
