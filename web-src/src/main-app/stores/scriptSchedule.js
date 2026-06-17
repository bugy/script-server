import {defineStore} from 'pinia'
import {axiosInstance} from '@/common/utils/axios_utils'
import clone from 'lodash/clone'
import {parametersToFormData} from '@/main-app/stores/mainStoreHelper'
import {useScriptSetupStore} from './scriptSetup'
import {useScriptConfigStore} from './scriptConfig'

export const useScriptScheduleStore = defineStore('scriptSchedule', {
    state: () => ({}),

    actions: {
        schedule({scheduleSetup}) {
            const parameterValues = clone(useScriptSetupStore().parameterValues)
            const scriptName = useScriptConfigStore().scriptConfig.name

            const formData = parametersToFormData(parameterValues)
            formData.append('__script_name', scriptName)
            formData.append('__schedule_config', JSON.stringify(scheduleSetup))

            return axiosInstance.post('schedule', formData)
                .catch(e => {
                    if (e.response.status === 422) e.userMessage = e.response.data
                    throw e
                })
        }
    }
})
