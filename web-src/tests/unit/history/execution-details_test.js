'use strict';
import ExecutionDetails from '@/common/components/history/execution-details'
import ReadOnlyField from '@/common/components/readonly-field';
import historyModule from '@/common/store/executions-module';
import {axiosInstance} from '@/common/utils/axios_utils';
import {mount} from '@vue/test-utils';
import MockAdapter from 'axios-mock-adapter';
import {createStore as createVuexStore} from 'vuex';
import {attachToDocument, createScriptServerTestVue, flushPromises, vueTicks} from '../test_utils';
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
        store = createVuexStore({
            modules: {
                history: historyModule()
            }
        });

        executionDetails = mount(ExecutionDetails, {
            attachTo: attachToDocument(),
            global: {plugins: [store]},
        });

        axiosMock = new MockAdapter(axiosInstance)

        await vueTicks();
    });

    afterEach(function () {
        executionDetails.unmount();
        axiosMock.restore()
    });

    describe('Test visualisation', function () {

            function assertField(fieldName, expectedValue) {
                // Vue 3 removed `vm.$children`; use VTU v2 findAllComponents instead.
                const foundChild = executionDetails.findAllComponents(ReadOnlyField)
                    .find(child => child.props('title') === fieldName);

                expect(foundChild).not.toBeNil()
                expect(foundChild.props('value')).toEqual(expectedValue)
            }

            function assertLog(expectedLog) {
                const actualLog = executionDetails.vm.$el.querySelector('code')?.textContent ?? '';
                expect(actualLog).toEqual(expectedLog)
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
