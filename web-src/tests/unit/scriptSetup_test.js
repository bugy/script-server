import scriptSetup from '@/main-app/store/scriptSetup';
import Vuex from 'vuex';
import cloneDeep from 'lodash/cloneDeep';
import {createScriptServerTestVue} from './test_utils'


const localVue = createScriptServerTestVue();
localVue.use(Vuex);

function createStore(sentData) {
    return new Vuex.Store({
        modules: {
            scriptSetup: cloneDeep(scriptSetup),
            scriptConfig: {
                namespaced: true,
                state: {
                    lastClientModelId: null
                },
                actions: {
                    sendParameterValue(_, {parameterName, value}) {
                        sentData.push(createSentValue(parameterName, value));
                    },
                    reloadModel({state}, {clientModelId}) {
                        state.lastClientModelId = clientModelId
                    }
                }
            }
        }
    });
}

function createSentValue(parameter, value) {
    return JSON.stringify({
        'event': 'parameterValue',
        data: {parameter, value}
    });
}

describe('Test scriptSetup module', function () {
    let sentData;
    let store;

    beforeEach(function () {
        sentData = [];

        store = createStore(sentData);
    });

    describe('Test send values', function () {
        it('Test send invalid parameter', function () {
            store.dispatch('scriptSetup/setParameterError', {parameterName: 'param1', errorMessage: 'Some problem'});
            store.dispatch('scriptSetup/setParameterValue', {parameterName: 'param1', value: 123});

            expect(sentData).toEqual([createSentValue('param1', null)])
        });

        it('Test send invalid parameter and then valid', function () {
            store.dispatch('scriptSetup/setParameterError', {parameterName: 'param1', errorMessage: 'Some problem'});
            store.dispatch('scriptSetup/setParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptSetup/setParameterError', {parameterName: 'param1', errorMessage: ''});
            store.dispatch('scriptSetup/setParameterValue', {parameterName: 'param1', value: 456});

            expect(sentData).toEqual([createSentValue('param1', null),
                createSentValue('param1', 456)])
        });
    });

    describe('Test initFromParameters', function () {
        it('Test single parameter with default', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}]);

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });

        it('Test single parameter with default, initialized again', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}])

            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 456}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });

        it('Test 2 parameters with default', function () {
            dispatchInitFromParameters('myScript',
                [{name: 'param1', default: 123}, {name: 'param2', default: 'hello'}]);

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test 2 parameters initialized sequentially', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}]);
            dispatchInitFromParameters('myScript', [{name: 'param2', default: 'hello'}]);

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test init parameters after reloadModel', async function () {
            store.dispatch('scriptSetup/reloadModel', {values: {'paramX': 'abc'}, scriptName: 's1'})
            dispatchInitFromParameters('s1', [{name: 'param1', default: 123}]);

            expect(store.state.scriptSetup.parameterValues).toEqual({'paramX': 'abc'});
        });

        it('Test init parameters after reloadModel after reset', function () {
            store.dispatch('scriptSetup/reloadModel', {values: {'paramX': 'abc'}, scriptName: 's1'})
            store.dispatch('scriptSetup/reset')
            dispatchInitFromParameters('s1', [{name: 'param1', default: 123}]);

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });
    });

    describe('Test forceValues', function () {
        it('Test forceValues after initFromParameters', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            expect(store.state.scriptSetup.forcedValueParameters).toEqual(['paramX', 'paramY']);
        })

        it('Test forceValues after initFromParameters without modelId', function () {
            const parameters = {paramX: 'hello', paramY: 123}
            store.dispatch('scriptSetup/reloadModel', {values: parameters, scriptName: 'abc', forceAllowedValues: true})

            store.dispatch('scriptSetup/initFromParameters', {
                scriptConfig: {name: 'abc'},
                parameters: [createDefaultParam('paramX'), createDefaultParam('paramY')]
            });

            expect(store.state.scriptSetup.forcedValueParameters).toEqual([]);
        })

        it('Test forceValues after initFromParameters with different scriptName', function () {
            const parameters = {paramX: 'hello', paramY: 123}

            store.dispatch('scriptSetup/reloadModel', {values: parameters, scriptName: 'ABC', forceAllowedValues: true})

            store.dispatch('scriptSetup/initFromParameters', {
                scriptConfig: {name: 'XYZ', clientModelId: store.state.scriptConfig.lastClientModelId},
                parameters: [createDefaultParam('paramX'), createDefaultParam('paramY')]
            });

            expect(store.state.scriptSetup.forcedValueParameters).toEqual([]);
        })

        it('Test forceValues and reload allowedValues', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            store.dispatch('scriptSetup/initFromParameters', {
                scriptConfig: {name: 'abc'},
                parameters: [
                    createDefaultParam('paramX'),
                    {name: 'paramY', values: [4, 5, 6]}]
            });

            expect(store.state.scriptSetup.forcedValueParameters).toEqual(['paramX']);
        })

        it('Test forceValues and setParameterValue', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            store.dispatch('scriptSetup/setParameterValue', {
                parameterName: 'paramX',
                value: 2
            });

            expect(store.state.scriptSetup.forcedValueParameters).toEqual(['paramY']);
        })

        function createDefaultParam(paramName) {
            return {name: paramName, values: [1, 2, 3]}
        }

        function reloadAndInit(scriptName, values, forceAllowedValues) {
            store.dispatch('scriptSetup/reloadModel', {values, scriptName, forceAllowedValues})

            const parameters = Object.keys(values).map(createDefaultParam)
            store.dispatch('scriptSetup/initFromParameters', {
                scriptConfig: {name: scriptName, clientModelId: store.state.scriptConfig.lastClientModelId},
                parameters
            });
        }
    })

    function dispatchInitFromParameters(scriptName, parameters) {
        store.dispatch('scriptSetup/initFromParameters', {
            scriptConfig: {name: scriptName, clientModelId: store.state.scriptConfig.lastClientModelId},
            parameters
        });
    }

})
