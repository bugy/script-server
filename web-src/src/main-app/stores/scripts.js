import {defineStore} from 'pinia'
import {isEmptyObject, isEmptyString, isNull} from '@/common/utils/common'
import {nextTick} from 'vue'
import router from '../router/router'
import {scriptNameToHash} from '../utils/model_helper'
import {axiosInstance} from '@/common/utils/axios_utils'

export const useScriptsStore = defineStore('scripts', {
    state: () => ({
        scripts: [],
        selectedScript: null,
        predefinedParameters: null
    }),
    actions: {
        init() {
            router.afterEach(() => this.selectScriptByHash())

            axiosInstance.get('scripts').then(({data}) => {
                const {scripts} = data
                scripts.sort((s1, s2) => s1.name.toLowerCase().localeCompare(s2.name.toLowerCase()))
                this.scripts = scripts
                this.selectScriptByHash()
            })
        },

        selectScriptByHash() {
            let encodedScriptName
            let queryParameters
            const currentRoute = router.currentRoute.value
            if (currentRoute.name === 'script') {
                encodedScriptName = currentRoute.params['scriptName']
                queryParameters = currentRoute.query
            } else {
                queryParameters = null
                encodedScriptName = null
            }

            let newSelectedScript = null
            for (const script of this.scripts) {
                const scriptHash = scriptNameToHash(script.name)
                if (scriptHash === encodedScriptName) {
                    newSelectedScript = script.name
                    break
                }
            }

            if (!isEmptyString(encodedScriptName) && isNull(newSelectedScript)) {
                newSelectedScript = encodedScriptName
            }

            if (isEmptyObject(queryParameters)) {
                queryParameters = null
            }

            this.selectedScript = newSelectedScript
            this.predefinedParameters = queryParameters

            if (!isEmptyObject(queryParameters)) {
                nextTick(() => router.replace({query: null}))
            }
        }
    }
})
