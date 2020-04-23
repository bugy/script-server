import scriptSetup from '@/main-app/store/scriptSetup';
import {createLocalVue} from '@vue/test-utils';
import {assert} from 'chai';
import Vuex from 'vuex';


const localVue = createLocalVue();
localVue.use(Vuex);

function createStore(sentData) {
    return new Vuex.Store({
        modules: {
            scriptSetup: scriptSetup,
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
});