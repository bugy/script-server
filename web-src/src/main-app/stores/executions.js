import {defineStore} from 'pinia'
import {axiosInstance} from '@/common/utils/axios_utils'
import {isEmptyArray, isEmptyString, isNull} from '@/common/utils/common'
import clone from 'lodash/clone'
import get from 'lodash/get'
import axios from 'axios'
import {createExecutor, STATUS_DISCONNECTED, STATUS_ERROR, STATUS_EXECUTING, STATUS_FINISHED, STATUS_INITIALIZING} from './scriptExecutor'
import {parametersToFormData} from '@/main-app/stores/mainStoreHelper'
import {saveParameterHistory} from '@/common/utils/parameterHistory'
import {useScriptsStore} from './scripts'
import {useScriptSetupStore} from './scriptSetup'
import {useScriptConfigStore} from './scriptConfig'

export const useExecutionsStore = defineStore('executions', {
    state: () => ({
        currentExecutor: null,
        executors: {}
    }),

    getters: {
        activeExecutors: (state) => Object.values(state.executors).filter(e =>
            e.state.status === STATUS_EXECUTING || e.state.status === STATUS_INITIALIZING
        ),
        hasActiveExecutors: (state, getters) => !isEmptyArray(getters.activeExecutors)
    },

    actions: {
        init() {
            axiosInstance.get('executions/active')
                .then(({data: activeExecutionIds}) => {
                    activeExecutionIds.sort((a, b) => parseInt(a) - parseInt(b))

                    const requests = activeExecutionIds.map(executionId =>
                        axiosInstance.get('executions/config/' + executionId)
                            .then(({data: config}) => {
                                const executor = createExecutor(executionId, config.scriptName, config.parameterValues)
                                executor.reconnect()
                                this.executors[executionId] = executor
                                return executor
                            })
                    )

                    if (!isNull(this.currentExecutor)) return

                    axios.all(requests)
                        .then(axios.spread((...executors) => {
                            if (!isNull(this.currentExecutor)) return
                            const selectedScript = useScriptsStore().selectedScript
                            if (isNull(selectedScript)) return
                            for (const executor of executors.filter(Boolean)) {
                                if (selectedScript === executor.state.scriptName) {
                                    this.selectExecutor(executor)
                                    break
                                }
                            }
                        }))
                        .catch(e => console.log(e))
                })
        },

        selectScript({selectedScript}) {
            const matching = Object.values(this.executors)
                .filter(e => e.state.scriptName === selectedScript)

            if (!isEmptyArray(matching)) {
                matching.sort((a, b) => parseInt(a.state.id) - parseInt(b.state.id))
                this.selectExecutor(matching[0])
            } else {
                this.selectExecutor(null)
            }
        },

        startExecution() {
            const parameterValues = clone(useScriptSetupStore().parameterValues)
            const scriptName = useScriptConfigStore().scriptConfig.name

            saveParameterHistory(scriptName, parameterValues)

            const formData = parametersToFormData(parameterValues)
            formData.append('__script_name', scriptName)

            const executor = createExecutor(null, scriptName, parameterValues)
            executor.setInitialising()
            this.selectExecutor(executor)

            axiosInstance.post('executions/start', formData)
                .then(({data: executionId}) => {
                    executor.start(executionId)
                    this.executors[executionId] = executor
                })
                .catch(error => {
                    const status = get(error, 'response.status')
                    let data = get(error, 'response.data')
                    if (isNull(error.response) || isEmptyString(data)) {
                        data = 'Connection error. Please contact the system administrator'
                    }
                    executor.setErrorStatus()
                    if (status !== 401) executor.appendLog('\n\n' + data)
                })
        },

        stopAll() {
            const active = this.activeExecutors
            if (isEmptyArray(active)) return Promise.resolve()

            return new Promise((resolve, reject) => {
                const msg = active.length === 1
                    ? 'Some script is running. Do you want to abort it?'
                    : active.length + ' scripts are running. Do you want to abort them?'

                if (!confirm(msg)) { reject(); return }

                Promise.all(active.map(e => e.abort()))
                    .catch(e => console.log('Failed to stop an executor: ' + e))
                    .finally(() => {
                        let retries = 0
                        const id = setInterval(() => {
                            if (retries > 20 || !this.hasActiveExecutors) {
                                resolve()
                                clearInterval(id)
                            }
                            retries++
                        }, 50)
                    })
            })
        },

        selectExecutor(executor) {
            const current = this.currentExecutor
            if (!isNull(current)) {
                if (executor && !isNull(executor.state.id) && executor.state.id === current.state.id) return
                if ([STATUS_FINISHED, STATUS_DISCONNECTED, STATUS_ERROR].includes(current.state.status)) {
                    this._removeExecutor(current)
                }
            }

            this.currentExecutor = executor
            if (executor) {
                useScriptSetupStore().reloadModel({
                    values: clone(executor.state.parameterValues),
                    forceAllowedValues: true,
                    scriptName: executor.state.scriptName
                })
            }
        },

        _removeExecutor(executor) {
            if (!(executor.state.id in this.executors)) return
            delete this.executors[executor.state.id]
            if (this.currentExecutor === executor) this.currentExecutor = null
        }
    }
})
