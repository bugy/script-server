import {defineStore} from 'pinia'
import {
    forEachKeyValue,
    guid,
    isEmptyObject,
    isEmptyString,
    isEmptyValue,
    isNull,
    removeElement
} from '@/common/utils/common'
import clone from 'lodash/clone'
import isEqual from 'lodash/isEqual'
import {getMostRecentValues, shouldUseHistoricalValues} from '@/common/utils/parameterHistory'
import {useScriptConfigStore} from './scriptConfig'

export const useScriptSetupStore = defineStore('scriptSetup', {
    state: () => ({
        parameterValues: {},
        forcedValueParameters: [],
        errors: {},
        nextReloadValues: null,
        _parameterAllowedValues: {},
        _defaultValuesFromConfig: {}
    }),

    actions: {
        reset() {
            this.errors = {}
            this.parameterValues = {}
            this.forcedValueParameters = []
            this.nextReloadValues = null
            this._defaultValuesFromConfig = {}
        },

        initFromParameters({scriptConfig, parameters}) {
            const oldAllowedValues = this._parameterAllowedValues

            this._parameterAllowedValues = parameters
                .filter(p => !isNull(p.values))
                .reduce((acc, p) => { acc[p.name] = p.values; return acc }, {})

            if (!isNull(this.nextReloadValues) && !isNull(scriptConfig)) {
                const {forceAllowedValues, parameterValues, scriptName: expectedScript, clientModelId: expectedId} = this.nextReloadValues

                if (expectedScript !== scriptConfig.name) {
                    this.nextReloadValues = null
                } else if (expectedId === scriptConfig.clientModelId) {
                    this.parameterValues = parameterValues
                    this.nextReloadValues = null
                    this.forcedValueParameters = forceAllowedValues ? Object.keys(parameterValues) : []
                    return
                }
            }

            this._updateForcedParameters(oldAllowedValues)

            if (!isEmptyObject(this.parameterValues)) {
                for (const parameter of parameters) {
                    const {name: parameterName} = parameter
                    const defaultValue = !isNull(parameter.default) ? parameter.default : null
                    const oldDefault = this._defaultValuesFromConfig[parameterName]
                    const currentValue = this.parameterValues[parameterName]

                    if (isEmptyValue(currentValue) || (!isNull(defaultValue) && oldDefault === currentValue)) {
                        this.setParameterValue({parameterName, value: defaultValue})
                    }
                    if (!isNull(defaultValue)) {
                        this._defaultValuesFromConfig[parameterName] = defaultValue
                    }
                }
                return
            }

            const historicalValues = scriptConfig ? getMostRecentValues(scriptConfig.name) : null
            const useHistory = historicalValues && shouldUseHistoricalValues(scriptConfig?.name)
            const values = {}

            for (const parameter of parameters) {
                const defaultValue = !isNull(parameter.default) ? parameter.default : null
                values[parameter.name] = useHistory && historicalValues.hasOwnProperty(parameter.name)
                    ? historicalValues[parameter.name]
                    : defaultValue
                if (!isNull(values[parameter.name])) {
                    this._defaultValuesFromConfig[parameter.name] = values[parameter.name]
                }
            }

            this._setAndSendParameterValues(values)
        },

        setParameterValue({parameterName, value}) {
            if (this.parameterValues[parameterName] !== value) {
                this.parameterValues[parameterName] = value
                removeElement(this.forcedValueParameters, parameterName)
            }
            this._sendValueToServer(parameterName, value)
        },

        setParameterError({parameterName, errorMessage}) {
            if (isEmptyString(errorMessage)) {
                delete this.errors[parameterName]
            } else {
                this.errors[parameterName] = errorMessage
            }
        },

        reloadModel({values, forceAllowedValues, scriptName}) {
            this.forcedValueParameters = []
            if (isEqual(this.parameterValues, values)) return

            const clientModelId = guid(16)
            this.parameterValues = values
            this.nextReloadValues = {parameterValues: values, forceAllowedValues, scriptName, clientModelId}

            useScriptConfigStore().reloadModel({scriptName, parameterValues: values, clientModelId})
        },

        _setAndSendParameterValues(values) {
            this.parameterValues = values
            forEachKeyValue(values, (parameterName, value) => this._sendValueToServer(parameterName, value))
        },

        _sendValueToServer(parameterName, value) {
            const valueToSend = (parameterName in this.errors) ? null : value
            useScriptConfigStore().sendParameterValue({parameterName, value: valueToSend})
        },

        _updateForcedParameters(oldAllowedValues) {
            const newAllowedValues = this._parameterAllowedValues
            for (const forced of clone(this.forcedValueParameters)) {
                const oldVals = oldAllowedValues[forced]
                const newVals = newAllowedValues[forced]
                if (isNull(oldVals) || isNull(newVals) || !isEqual(oldVals, newVals)) {
                    removeElement(this.forcedValueParameters, forced)
                }
            }
        }
    }
})
