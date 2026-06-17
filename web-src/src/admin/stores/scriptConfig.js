import {defineStore} from 'pinia'
import {UPLOAD_MODE} from '@/admin/components/scripts-config/script-edit/ScriptEditDialog'
import {axiosInstance} from '@/common/utils/axios_utils'
import {contains, forEachKeyValue, isEmptyArray, isEmptyValue} from '@/common/utils/common'
import clone from 'lodash/clone'
import router from '../router/router'

export const NEW_SCRIPT = '_new'

const allowedEmptyValuesInParam = ['name']

function removeEmptyValues(config) {
    if (isEmptyArray(config.parameters)) return

    for (const parameter of config.parameters) {
        let emptyValueKeys = []
        forEachKeyValue(parameter, (key, value) => {
            if (!contains(allowedEmptyValuesInParam, key) && isEmptyValue(value)) {
                emptyValueKeys.push(key)
            }
        })
        emptyValueKeys.forEach(key => delete parameter[key])
    }
}

function prepareConfigForSave(scriptConfig, scriptFilename) {
    const config = clone(scriptConfig)
    removeEmptyValues(config)

    const formData = new FormData()
    if (config['script']['mode'] === UPLOAD_MODE) {
        formData.append('uploadedScript', config['script']['uploadFile'])
        delete config['script']['uploadFile']
    }
    formData.append('config', JSON.stringify(config))
    formData.append('filename', scriptFilename)
    return formData
}

export const useAdminScriptConfigStore = defineStore('adminScriptConfig', {
    state: () => ({
        scriptName: null,
        scriptConfig: null,
        scriptFilename: null,
        error: null,
        isNew: false
    }),
    actions: {
        init(scriptName) {
            if (scriptName === NEW_SCRIPT) {
                this.scriptName = null
                this.scriptConfig = {parameters: []}
                this.isNew = true
                this.scriptFilename = null
                this.error = null
                return
            }

            this.scriptName = scriptName
            this.scriptConfig = null
            this.scriptFilename = null
            this.error = null
            this.isNew = false

            axiosInstance.get('admin/scripts/' + encodeURIComponent(scriptName))
                .then(({data}) => {
                    this.error = null
                    this.scriptConfig = data.config
                    this.scriptFilename = data.filename
                    this.isNew = false
                })
                .catch(() => {
                    this.error = 'Failed to load script config'
                    this.scriptConfig = null
                    this.scriptFilename = null
                })
        },

        save() {
            const oldName = this.scriptName
            const newName = this.scriptConfig.name
            const formData = prepareConfigForSave(this.scriptConfig, this.scriptFilename)
            const axiosAction = this.isNew ? axiosInstance.post : axiosInstance.put

            return axiosAction('admin/scripts', formData)
                .then(() => {
                    if (oldName === newName) {
                        this.init(newName)
                    } else {
                        router.push({path: `/scripts/${encodeURIComponent(newName)}`})
                    }
                })
                .catch(e => {
                    if ((e.response.status === 422) || (e.response.status === 403)) {
                        e.userMessage = e.response.data
                    }
                    throw e
                })
        },

        deleteScript() {
            const oldName = this.scriptName
            return axiosInstance.delete(`admin/scripts/${encodeURIComponent(oldName)}`)
                .then(() => router.push({path: '/scripts/'}))
                .catch(e => {
                    if (e.response.status === 422) e.userMessage = e.response.data
                    throw e
                })
        }
    }
})
