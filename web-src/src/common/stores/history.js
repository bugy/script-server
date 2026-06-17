import {defineStore} from 'pinia'
import {isEmptyString, isNull, logError} from '@/common/utils/common'
import {axiosInstance} from '@/common/utils/axios_utils'

export const useHistoryStore = defineStore('history', {
    state: () => ({
        executions: [],
        selectedExecution: null,
        selectedExecutionId: null,
        loading: false,
        detailsLoading: false
    }),
    actions: {
        init() {
            this.loading = true
            this.selectedExecution = null
            this.selectedExecutionId = null

            axiosInstance.get('history/execution_log/short').then(({data}) => {
                sortExecutionLogs(data)
                this.executions = data.map(log => translateExecutionLog(log))
                this.loading = false
            })
        },

        selectExecution(executionId) {
            if (isEmptyString(executionId)) {
                this.selectedExecutionId = executionId
                this.selectedExecution = null
                this.detailsLoading = false
                return
            }

            let execution = this.executions.find(e => e.id === executionId)
            if (isNull(execution)) {
                execution = {id: executionId, user: 'Unknown', script: 'Unknown'}
            }
            this.selectedExecutionId = executionId
            this.selectedExecution = execution
            this.detailsLoading = true

            axiosInstance.get('history/execution_log/long/' + executionId)
                .then(({data: incomingLog}) => {
                    if (executionId !== this.selectedExecutionId) return
                    this.selectedExecution = translateExecutionLog(incomingLog)
                    this.detailsLoading = false
                })
                .catch(error => logError(error))
        }
    }
})

function sortExecutionLogs(logs) {
    logs.sort(function (v1, v2) {
        if (isNull(v1.startTime)) {
            return isNull(v2.startTime) ? v1.user.localeCompare(v2.user) : 1
        } else if (isNull(v2.startTime)) {
            return -1
        }
        const dateCompare = Date.parse(v2.startTime) - Date.parse(v1.startTime)
        return dateCompare !== 0 ? dateCompare : v1.user.localeCompare(v2.user)
    })
}

export function translateExecutionLog(log) {
    log.startTimeString = getStartTimeString(log)
    log.fullStatus = getFullStatus(log)
    return log
}

function getStartTimeString(log) {
    if (!isNull(log.startTime)) {
        const startTime = new Date(log.startTime)
        return startTime.toLocaleDateString() + ' ' + startTime.toLocaleTimeString()
    }
    return ''
}

function getFullStatus(log) {
    if (!isNull(log.exitCode) && !isNull(log.status)) {
        return log.status + ' (' + log.exitCode + ')'
    } else if (!isNull(log.status)) {
        return log.status
    }
}
