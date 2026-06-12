import {defineStore} from 'pinia'
import {ReactiveWebSocket} from '@/common/connections/rxWebsocket'
import {axiosInstance} from '@/common/utils/axios_utils'
import {
    contains,
    forEachKeyValue,
    HttpForbiddenError,
    HttpRequestError,
    HttpUnauthorizedError,
    isEmptyObject,
    isEmptyString,
    isNull,
    logError,
    removeElement,
    SocketClosedError,
    toDict,
    toQueryArgs
} from '@/common/utils/common'
import clone from 'lodash/clone'
import {preprocessParameter} from '../utils/model_helper'
import {useScriptsStore} from './scripts'

export const NOT_FOUND_ERROR_PREFIX = `Failed to find the script`
export const CANNOT_PARSE_ERROR_PREFIX = `Cannot parse script config file`

const internalState = {
    websocket: null,
    reconnectionAttempt: 0
}

export const useScriptConfigStore = defineStore('scriptConfig', {
    state: () => ({
        scriptConfig: null,
        loadError: null,
        parameters: [],
        sentValues: {},
        loading: false,
        clientStateVersion: 0,
        preloadScript: null
    }),

    actions: {
        reloadScript(selectedScript) {
            this._setConnection(null)
            this._resetConfig()
            if (!isEmptyString(selectedScript)) {
                this.loading = true
                reconnect(this, selectedScript)
            }
        },

        reloadModel({scriptName, parameterValues, clientModelId}) {
            if (useScriptsStore().selectedScript === scriptName) {
                this.loading = true
                _sendReloadModelRequest(parameterValues, clientModelId, internalState.websocket)
                this.sentValues = clone(parameterValues)
            }
        },

        sendParameterValue({parameterName, value}) {
            const websocket = internalState.websocket
            if (isNull(websocket) || websocket.isClosed()) return

            const newStateVersion = this.clientStateVersion + 1
            this.clientStateVersion = newStateVersion

            if (this.sentValues[parameterName] !== value) {
                for (const parameter of this.parameters) {
                    if (parameter.requiredParameters?.includes(parameterName)) {
                        parameter.loading = true
                        parameter.awaitedVersion = newStateVersion
                    }
                }
                this.sentValues[parameterName] = value
                _sendParameterValue(parameterName, value, websocket, newStateVersion)
            }
        },

        resendValues() {
            const websocket = internalState.websocket
            if (isNull(websocket) || websocket.isClosed()) return
            forEachKeyValue(this.sentValues, (key, value) => _sendParameterValue(key, value, websocket))
        },

        _setConnection(websocket) {
            const existing = internalState.websocket
            if (!isNull(existing) && !existing.isClosed()) existing.close()
            internalState.websocket = websocket
        },

        _resetConfig() {
            internalState.reconnectionAttempt = 0
            this.scriptConfig = null
            this.parameters = []
            this.loadError = null
            this.loading = false
            this.sentValues = {}
            this.preloadScript = null
        },

        _updateScriptConfig(config) {
            this.scriptConfig = config
            const newParameters = config.parameters
            for (const parameter of newParameters) {
                _preprocessParam(parameter, this.scriptConfig)
            }

            if (this.parameters.length === 0) {
                this.parameters = newParameters
                return
            }

            const oldDict = toDict(this.parameters, 'name')
            const newDict = toDict(newParameters, 'name')

            forEachKeyValue(oldDict, (name, parameter) => {
                if (!(name in newDict)) removeElement(this.parameters, parameter)
            })

            forEachKeyValue(newDict, (name, parameter) => {
                if (name in oldDict) {
                    const index = this.parameters.indexOf(oldDict[name])
                    this.parameters[index] = parameter
                } else {
                    this.parameters.push(parameter)
                }
            })
        },

        _addParameter(parameter) {
            _preprocessParam(parameter, this.scriptConfig)
            this.parameters.push(parameter)
        },

        _updateParameter(parameter) {
            const parameters = this.parameters
            const idx = parameters.findIndex(p => p.name === parameter.name)
            if (idx < 0) { console.log('Failed to find parameter ' + parameter.name); return }
            parameter.loading = parameters[idx].loading
            parameter.awaitedVersion = parameters[idx].awaitedVersion
            _preprocessParam(parameter, this.scriptConfig)
            parameters[idx] = parameter
        },

        _removeParameter(parameterName) {
            const idx = this.parameters.findIndex(p => p.name === parameterName)
            if (idx >= 0) this.parameters.splice(idx, 1)
        },

        _resetAwaitedDependencies(clientStateVersion, singleParameterName) {
            if (!clientStateVersion) return
            for (const parameter of this.parameters) {
                if (!isNull(singleParameterName) && parameter.name !== singleParameterName) continue
                if (parameter.awaitedVersion && parameter.awaitedVersion <= clientStateVersion) {
                    parameter.loading = false
                    parameter.awaitedVersion = null
                }
            }
        }
    }
})

function _sendParameterValue(parameterName, value, websocket, newStateVersion) {
    websocket.send(JSON.stringify({
        event: 'parameterValue',
        data: {parameter: parameterName, value, clientStateVersion: newStateVersion}
    }))
}

function _sendReloadModelRequest(parameterValues, clientModelId, websocket) {
    websocket.send(JSON.stringify({
        event: 'reloadModelValues',
        data: {parameterValues, clientModelId}
    }))
}

function _preprocessParam(parameter, scriptConfig) {
    preprocessParameter(parameter, (path) => {
        if (isNull(scriptConfig)) throw Error('Config is not available')
        const encodedScript = encodeURIComponent(scriptConfig.name)
        const encodedParameter = encodeURIComponent(parameter.name)
        const url = `scripts/${encodedScript}/${encodedParameter}/list-files`
        const param = toQueryArgs({'path': path, 'id': scriptConfig.id})
        return axiosInstance.get(url + '?' + param).then(({data}) => data)
    })
}

function reconnect(store, selectedScript) {
    const initWithValues = !isNull(store.scriptConfig) && !isEmptyObject(store.sentValues)
    const uri = 'scripts/' + encodeURIComponent(selectedScript) + '?initWithValues=' + initWithValues

    const socket = new ReactiveWebSocket(uri, {
        onNext(rawMessage) {
            internalState.reconnectionAttempt = 0
            const event = JSON.parse(rawMessage)
            const eventType = event.event
            const data = event.data
            const clientStateVersion = data.clientStateVersion

            if (contains(['initialConfig', 'reloadedConfig', 'clientStateVersionAccepted'], eventType)) {
                store._resetAwaitedDependencies(clientStateVersion, null)
            } else if (eventType === 'parameterChanged') {
                store._resetAwaitedDependencies(clientStateVersion, data?.name)
            }

            if (isNull(store.scriptConfig) && eventType !== 'initialConfig') {
                console.error('Expected "initialConfig" event, but got ' + eventType)
                store.loadError = 'Unexpected error occurred'
                store.loading = false
                socket.close()
                return
            }

            if (eventType === 'initialConfig') {
                store._updateScriptConfig(data)
                store.loading = false
                store.resendValues()
                return
            }

            if (eventType === 'reloadedConfig') {
                store._updateScriptConfig(data)
                store.loading = false
                return
            }

            if (eventType === 'parameterChanged') { store._updateParameter(data); return }
            if (eventType === 'parameterAdded') { store._addParameter(data); return }
            if (eventType === 'parameterRemoved') { store._removeParameter(data.parameterName); return }
            if (eventType === 'preloadScript') { store.preloadScript = data }
        },

        onError(error) {
            logError(error)

            if (error instanceof SocketClosedError) {
                if (error.code === 422) {
                    store.loadError = `${error.reason} "${selectedScript}"`
                    store.loading = false
                    return
                }
                console.log('Socket closed. code=' + error.code + ', reason=' + error.reason)
                if (isNull(store.scriptConfig)) {
                    store.loadError = 'Failed to connect to the server'
                    store.loading = false
                    return
                }
                internalState.reconnectionAttempt++
                if (internalState.reconnectionAttempt > 5) {
                    store.loadError = 'Failed to reconnect'
                    store.loading = false
                    return
                }
                setTimeout(() => {
                    console.log('Trying to reconnect. Attempt ' + internalState.reconnectionAttempt)
                    reconnect(store, selectedScript)
                }, (internalState.reconnectionAttempt - 1) * 500)
                return
            }

            if (error instanceof HttpForbiddenError) { store.loadError = 'Access to the script is denied'; store.loading = false; return }
            if (error instanceof HttpUnauthorizedError) { store.loadError = 'Failed to authenticate the user'; store.loading = false; return }
            if ((error instanceof HttpRequestError) && error.code === 404) {
                store.loadError = `${NOT_FOUND_ERROR_PREFIX} "${selectedScript}"`
                store.loading = false
                return
            }
            store.loadError = 'Unexpected error occurred'
            store.loading = false
        },

        onComplete() {
            console.log('Websocket completed. This should not be possible for a config socket')
            store.loadError = 'Connection to server closed'
            store.loading = false
        }
    })

    if (initWithValues) {
        socket.send(JSON.stringify({
            event: 'initialValues',
            data: {parameterValues: store.sentValues}
        }))
    }

    store._setConnection(socket)
}
