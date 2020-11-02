import axios from 'axios';
import clone from 'lodash/clone';
import {parametersToFormData} from "@/main-app/store/mainStoreHelper";

export const axiosInstance = axios.create();

export default {
    state: {},
    namespaced: true,
    actions: {
        schedule({state, commit, dispatch, rootState}, {scheduleSetup}) {
            const parameterValues = clone(rootState.scriptSetup.parameterValues);
            const scriptName = rootState.scriptConfig.scriptConfig.name;

            const formData = parametersToFormData(parameterValues);
            formData.append('__script_name', scriptName);
            formData.append('__schedule_config', JSON.stringify(scheduleSetup))

            return axiosInstance.post('schedule', formData)
                .catch(e => {
                    if (e.response.status === 422) {
                        e.userMessage = e.response.data;
                    }
                    throw e;
                });
        },
    }
}
