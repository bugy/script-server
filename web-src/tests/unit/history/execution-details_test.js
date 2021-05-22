'use strict';
import ExecutionDetails from '@/common/components/history/execution-details'
import historyModule from '@/common/store/executions-module';
import {axiosInstance} from '@/common/utils/axios_utils';
import {mount} from '@vue/test-utils';
import MockAdapter from 'axios-mock-adapter';
import {assert, config as chaiConfig} from 'chai';
import Vuex from 'vuex';
import {attachToDocument, createScriptServerTestVue, flushPromises, vueTicks} from '../test_utils';


chaiConfig.truncateThreshold = 0;

const localVue = createScriptServerTestVue();
localVue.use(Vuex);

let axiosMock;


function mockGetExecution(id, startTime, user, script, status, exitCode, command, log, outputFormat = null) {
    axiosMock.onGet('history/execution_log/long/' + id)
        .reply(200, {
            id, startTime, user, script, status, exitCode, command, log, outputFormat
        });
}

describe('Test history details', function () {
    let executionDetails;
    let store;

    beforeEach(async function () {
        store = new Vuex.Store({
            modules: {
                history: historyModule()
            }
        });

        executionDetails = mount(ExecutionDetails, {
            attachTo: attachToDocument(),
            store,
            localVue
        });

        axiosMock = new MockAdapter(axiosInstance)

        await vueTicks();
    });

    afterEach(function () {
        executionDetails.destroy();
        axiosMock.restore()
    });

    describe('Test visualisation', function () {

            function assertField(fieldName, expectedValue) {
                const foundChild = executionDetails.vm.$children.find(child =>
                    (child.$options._componentTag === 'readonly-field')
                    && (child.$props.title === fieldName));

                assert.exists(foundChild, 'Failed to find field ' + fieldName);
                assert.equal(foundChild.$props.value, expectedValue);
            }

            function assertLog(expectedLog) {
                const actualLog = $(executionDetails.vm.$el).find('code').text();
                assert.equal(actualLog, expectedLog);
            }

            it('test null execution', function () {
                assertField('Script name', '');
                assertField('User', '');
                assertField('Start time', '');
                assertField('Status', '');
                assertField('Command', '');
                assertLog('');
            });

            it('test some execution', async function () {
                mockGetExecution('12345',
                    '2019-12-25T12:30:01',
                    'User X',
                    'My script',
                    'Finished',
                    -15,
                    'my_script.sh -a -b 2',
                    'some long log text');

                executionDetails.setProps({'executionId': 12345});

                await flushPromises();
                await vueTicks();

                assertField('Script name', 'My script');
                assertField('User', 'User X');
                assertField('Start time', '12/25/2019 12:30:01 PM');
                assertField('Status', 'Finished (-15)');
                assertField('Command', 'my_script.sh -a -b 2');
                assertLog('some long log text');
            });

            it('test some execution changed to null', async function () {
                mockGetExecution('12345',
                    '2019-12-25T12:30:01',
                    'User X',
                    'My script',
                    'Finished',
                    -15,
                    'my_script.sh -a -b 2',
                    'some long log text');

                executionDetails.setProps({'executionId': 12345});
                await flushPromises();
                await vueTicks();

                executionDetails.setProps({'executionId': null});

                await flushPromises();
                await vueTicks();

                assertField('Script name', '');
                assertField('User', '');
                assertField('Start time', '');
                assertField('Status', '');
                assertField('Command', '');
                assertLog('');
            });

            it('test outputFormat', async function () {
                mockGetExecution('12345',
                    '2019-12-25T12:30:01',
                    'User X',
                    'My script',
                    'Finished',
                    -15,
                    'my_script.sh -a -b 2',
                    '<b>some bold text</b>',
                    'html');

                executionDetails.setProps({'executionId': 12345});
                await flushPromises();
                await vueTicks();

                const boldElement = executionDetails.get('b')
                expect(boldElement.text()).toBe('some bold text')
            });
        }
    )
});
