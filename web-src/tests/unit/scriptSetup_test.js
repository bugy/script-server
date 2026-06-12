import {createPinia, setActivePinia} from 'pinia';
import {createScriptServerTestVue} from './test_utils'
import {useScriptSetupStore} from '@/main-app/stores/scriptSetup';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';

function createSentValue(parameter, value) {
    return JSON.stringify({
        'event': 'parameterValue',
        data: {parameter, value}
    });
}

describe('Test scriptSetup module', function () {
    let store;
    let sentData;
    let scriptConfigState;

    beforeEach(function () {
        sentData = [];
        scriptConfigState = {lastClientModelId: null};

        setActivePinia(createPinia());

        // Spy on scriptConfig so scriptSetup's require('./scriptConfig').useScriptConfigStore()
        // returns our intercepted store instance via the active Pinia.
        const scriptConfig = useScriptConfigStore();
        vi.spyOn(scriptConfig, 'sendParameterValue').mockImplementation(({parameterName, value}) => {
            sentData.push(createSentValue(parameterName, value));
        });
        vi.spyOn(scriptConfig, 'reloadModel').mockImplementation(({scriptName, parameterValues, clientModelId}) => {
            scriptConfigState.lastClientModelId = clientModelId;
        });

        store = useScriptSetupStore();
    });

    afterEach(function () {
        vi.restoreAllMocks();
    });

    describe('Test send values', function () {
        it('Test send invalid parameter', function () {
            store.setParameterError({parameterName: 'param1', errorMessage: 'Some problem'});
            store.setParameterValue({parameterName: 'param1', value: 123});

            expect(sentData).toEqual([createSentValue('param1', null)])
        });

        it('Test send invalid parameter and then valid', function () {
            store.setParameterError({parameterName: 'param1', errorMessage: 'Some problem'});
            store.setParameterValue({parameterName: 'param1', value: 123});
            store.setParameterError({parameterName: 'param1', errorMessage: ''});
            store.setParameterValue({parameterName: 'param1', value: 456});

            expect(sentData).toEqual([createSentValue('param1', null),
                createSentValue('param1', 456)])
        });
    });

    describe('Test initFromParameters', function () {
        it('Test single parameter with default', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}]);

            expect(store.parameterValues).toEqual({'param1': 123});
        });

        it('Test single parameter with default, initialized again', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}])

            store.setParameterValue({
                parameterName: 'param1',
                value: 12
            });

            store.initFromParameters({
                scriptConfig: {name: 'myScript'},
                parameters: [{name: 'param1', default: 456}]
            });

            expect(store.parameterValues).toEqual({'param1': 12});
        });

        it('Test single parameter with default, initialized again, when value is different', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}])

            store.initFromParameters({
                scriptConfig: {name: 'myScript'},
                parameters: [{name: 'param1', default: 456}]
            });

            expect(store.parameterValues).toEqual({'param1': 456});
        });

        it('Test 2 parameters with default', function () {
            dispatchInitFromParameters('myScript',
                [{name: 'param1', default: 123}, {name: 'param2', default: 'hello'}]);

            expect(store.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test 2 parameters initialized sequentially', function () {
            dispatchInitFromParameters('myScript', [{name: 'param1', default: 123}]);
            dispatchInitFromParameters('myScript', [{name: 'param2', default: 'hello'}]);

            expect(store.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test init parameters after reloadModel', async function () {
            store.reloadModel({values: {'paramX': 'abc'}, scriptName: 's1'})
            dispatchInitFromParameters('s1', [{name: 'param1', default: 123}]);

            expect(store.parameterValues).toEqual({'paramX': 'abc'});
        });

        it('Test init parameters after reloadModel after reset', function () {
            store.reloadModel({values: {'paramX': 'abc'}, scriptName: 's1'})
            store.reset()
            dispatchInitFromParameters('s1', [{name: 'param1', default: 123}]);

            expect(store.parameterValues).toEqual({'param1': 123});
        });
    });

    describe('Test forceValues', function () {
        it('Test forceValues after initFromParameters', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            expect(store.forcedValueParameters).toEqual(['paramX', 'paramY']);
        })

        it('Test forceValues after initFromParameters without modelId', function () {
            const parameters = {paramX: 'hello', paramY: 123}
            store.reloadModel({values: parameters, scriptName: 'abc', forceAllowedValues: true})

            store.initFromParameters({
                scriptConfig: {name: 'abc'},
                parameters: [createDefaultParam('paramX'), createDefaultParam('paramY')]
            });

            expect(store.forcedValueParameters).toEqual([]);
        })

        it('Test forceValues after initFromParameters with different scriptName', function () {
            const parameters = {paramX: 'hello', paramY: 123}

            store.reloadModel({values: parameters, scriptName: 'ABC', forceAllowedValues: true})

            store.initFromParameters({
                scriptConfig: {name: 'XYZ', clientModelId: scriptConfigState.lastClientModelId},
                parameters: [createDefaultParam('paramX'), createDefaultParam('paramY')]
            });

            expect(store.forcedValueParameters).toEqual([]);
        })

        it('Test forceValues and reload allowedValues', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            store.initFromParameters({
                scriptConfig: {name: 'abc'},
                parameters: [
                    createDefaultParam('paramX'),
                    {name: 'paramY', values: [4, 5, 6]}]
            });

            expect(store.forcedValueParameters).toEqual(['paramX']);
        })

        it('Test forceValues and setParameterValue', function () {
            reloadAndInit('abc', {paramX: 'hello', paramY: 123}, true)

            store.setParameterValue({
                parameterName: 'paramX',
                value: 2
            });

            expect(store.forcedValueParameters).toEqual(['paramY']);
        })

        function createDefaultParam(paramName) {
            return {name: paramName, values: [1, 2, 3]}
        }

        function reloadAndInit(scriptName, values, forceAllowedValues) {
            store.reloadModel({values, scriptName, forceAllowedValues})

            const parameters = Object.keys(values).map(createDefaultParam)
            store.initFromParameters({
                scriptConfig: {name: scriptName, clientModelId: scriptConfigState.lastClientModelId},
                parameters
            });
        }
    })

    function dispatchInitFromParameters(scriptName, parameters) {
        store.initFromParameters({
            scriptConfig: {name: scriptName, clientModelId: scriptConfigState.lastClientModelId},
            parameters
        });
    }

})
