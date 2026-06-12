import {reactive} from 'vue'
import {axiosInstance} from '@/common/utils/axios_utils'
import {getWebsocketUrl, isNull, isWebsocketClosed} from '@/common/utils/common'

export const STATUS_INITIALIZING = 'initializing'
export const STATUS_EXECUTING = 'executing'
export const STATUS_FINISHED = 'finished'
export const STATUS_DISCONNECTED = 'disconnected'
export const STATUS_ERROR = 'error'

export function createExecutor(id, scriptName, parameterValues) {
    const ws = {socket: null}

    const executor = reactive({
        state: {
            id,
            scriptName,
            parameterValues,
            logChunks: [],
            inputPromptText: null,
            downloadableFiles: [],
            inlineImages: {},
            status: STATUS_INITIALIZING,
            killIntervalId: null,
            killTimeoutSec: null,
            killEnabled: false
        },

        setStatus(status) {
            if (!isNull(executor.state.killIntervalId)) {
                clearInterval(executor.state.killIntervalId)
                executor.state.killIntervalId = null
                executor.state.killTimeoutSec = null
                executor.state.killEnabled = false
            }
            executor.state.status = status
        },

        setInitialising() {
            executor.state.logChunks = ['Calling the script...']
            executor.setStatus(STATUS_INITIALIZING)
        },

        setErrorStatus() {
            executor.setStatus(STATUS_ERROR)
        },

        appendLog(log) {
            executor.state.logChunks.push(log)
        },

        reconnect() {
            executor.setStatus(STATUS_EXECUTING)
            attachToWebsocket(ws, executor)
        },

        start(executionId) {
            executor.state.id = executionId
            executor.state.logChunks = []
            executor.setStatus(STATUS_EXECUTING)
            attachToWebsocket(ws, executor)
        },

        stopExecution() {
            if (isNull(executor.state.killIntervalId) && !executor.state.killEnabled) {
                const intervalId = setInterval(() => executor._tickKill(), 1000)
                executor.state.killIntervalId = intervalId
                executor.state.killTimeoutSec = 5
                executor.state.killEnabled = false
            }
            return axiosInstance.post('executions/stop/' + executor.state.id)
        },

        killExecution() {
            return axiosInstance.post('executions/kill/' + executor.state.id)
        },

        sendUserInput(userInput) {
            if (!isNull(ws.socket) && !isWebsocketClosed(ws.socket)) {
                ws.socket.send(userInput)
            }
        },

        cleanup() {
            axiosInstance.post('executions/cleanup/' + executor.state.id)
        },

        abort() {
            return executor.stopExecution()
        },

        _tickKill() {
            if (executor.state.status !== STATUS_EXECUTING) {
                clearInterval(executor.state.killIntervalId)
                executor.state.killIntervalId = null
                executor.state.killTimeoutSec = null
                executor.state.killEnabled = false
                return
            }
            if (executor.state.killTimeoutSec <= 1) {
                clearInterval(executor.state.killIntervalId)
                executor.state.killIntervalId = null
                executor.state.killTimeoutSec = null
                executor.state.killEnabled = true
                return
            }
            executor.state.killTimeoutSec--
        }
    })

    return executor
}

function attachToWebsocket(ws, executor) {
    if (!isNull(ws.socket)) return

    const executionId = executor.state.id
    let socket
    try {
        socket = new WebSocket(getWebsocketUrl('executions/io/' + executionId))
    } catch (e) {
        console.log('Failed to open websocket')
        return
    }

    socket.addEventListener('message', (message) => {
        const event = JSON.parse(message.data)
        if (event.event === 'output') {
            executor.state.logChunks.push(event.data)
        } else if (event.event === 'input') {
            executor.state.inputPromptText = event.data
        } else if (event.event === 'file') {
            executor.state.downloadableFiles.push({url: event.data.url, filename: event.data.filename})
        } else if (event.event === 'inline-image') {
            executor.state.inlineImages[event.data.output_path] = event.data.download_url
        }
    })

    socket.addEventListener('close', (event) => {
        if (event.code === 1000) {
            executor.setStatus(STATUS_FINISHED)
        } else {
            axiosInstance.get('executions/status/' + executionId)
                .then(({data: status}) => {
                    executor.setStatus(status === 'finished' ? STATUS_FINISHED : STATUS_DISCONNECTED)
                })
                .catch(() => executor.setErrorStatus())
        }
    })

    ws.socket = socket
}
