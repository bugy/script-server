import {defineStore} from 'pinia'
import {axiosInstance} from '@/common/utils/axios_utils'

export const useAdminScriptsStore = defineStore('adminScripts', {
    state: () => ({
        scripts: [],
        loading: false
    }),
    actions: {
        init() {
            this.loading = true
            axiosInstance.get('scripts', {params: {mode: 'edit'}}).then(({data}) => {
                const {scripts} = data
                let scriptConfigs = scripts.map(s => ({name: s.name, parsingFailed: s.parsing_failed}))
                scriptConfigs.sort((e1, e2) => e1.name.toLowerCase().localeCompare(e2.name.toLowerCase()))
                this.scripts = scriptConfigs
                this.loading = false
            })
        }
    }
})
