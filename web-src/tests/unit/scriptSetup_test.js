import scriptSetup from '@/main-app/store/scriptSetup';
import {createLocalVue} from '@vue/test-utils';
import {assert} from 'chai';
import Vuex from 'vuex';
import cloneDeep from 'lodash/cloneDeep';


const localVue = createLocalVue();
localVue.use(Vuex);

function createStore(sentData) {
    return new Vuex.Store({
        modules: {
            scriptSetup: cloneDeep(scriptSetup),
            scriptConfig: {
                namespaced: true,
                actions: {
                    sendParameterValue(_, {parameterName, value}) {
                        sentData.push(createSentValue(parameterName, value));
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

            assert.deepEqual(sentData, [createSentValue('param1', null)]);
        });

        it('Test send invalid parameter and then valid', function () {
            store.dispatch('scriptSetup/setParameterError', {parameterName: 'param1', errorMessage: 'Some problem'});
            store.dispatch('scriptSetup/setParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptSetup/setParameterError', {parameterName: 'param1', errorMessage: ''});
            store.dispatch('scriptSetup/setParameterValue', {parameterName: 'param1', value: 456});

            assert.deepEqual(sentData, [createSentValue('param1', null),
                createSentValue('param1', 456)]);
        });
    });

    describe('Test initFromParameters', function () {
        it('Test single parameter with default', function () {
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 123}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });

        it('Test single parameter with default, initialized again', function () {
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 123}]
            });
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 456}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });

        it('Test 2 parameters with default', function () {
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 123}, {name: 'param2', default: 'hello'}]
            });


            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test 2 parameters initialized sequentially', function () {
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param1', default: 123}]
            });
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 'myScript',
                parameters: [{name: 'param2', default: 'hello'}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123, 'param2': 'hello'});
        });

        it('Test init parameters after setParameterValues', function () {
            store.dispatch('scriptSetup/setParameterValues', {values: {'paramX': 'abc'}, scriptName: 's1'})
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 's1',
                parameters: [{name: 'param1', default: 123}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'paramX': 'abc'});
        });

        it('Test init parameters after setParameterValues after reset', function () {
            store.dispatch('scriptSetup/setParameterValues', {values: {'paramX': 'abc'}, scriptName: 's1'})
            store.dispatch('scriptSetup/reset')
            store.dispatch('scriptSetup/initFromParameters', {
                scriptName: 's1',
                parameters: [{name: 'param1', default: 123}]
            });

            expect(store.state.scriptSetup.parameterValues).toEqual({'param1': 123});
        });
    });
});