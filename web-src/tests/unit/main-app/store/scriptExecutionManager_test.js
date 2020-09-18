import {isNull} from '@/common/utils/common';
import scriptExecutionManagerModule, {
    __RewireAPI__ as ExecutionManagerRewire,
    axiosInstance
} from '@/main-app/store/scriptExecutionManager';
import {STATUS_INITIALIZING} from '@/main-app/store/scriptExecutor';
import {createLocalVue} from '@vue/test-utils';
import MockAdapter from 'axios-mock-adapter';
import cloneDeep from 'lodash/cloneDeep';
import {WebSocket} from 'mock-socket';
import Vuex from 'vuex';
import {flushPromises} from '../../test_utils';

const axiosMock = new MockAdapter(axiosInstance);
window.WebSocket = WebSocket;

const localVue = createLocalVue();
localVue.use(Vuex);

ExecutionManagerRewire.__Rewire__('scriptExecutor', createMockExecutor);

function createStore() {
    return new Vuex.Store({
        modules: {
            executions: cloneDeep(scriptExecutionManagerModule),
            scripts: {
                selectedScript: null
            },
            scriptSetup: {
                namespaced: true,
                state: {
                    parameterValues: {}
                },
                actions: {
                    setParameterValues({state}, valuesHolder) {
                        state.parameterValues = valuesHolder.values;
                    }
                }
            },
            scriptConfig: {
                state: {
                    scriptConfig: {
                        name: 'abc'
                    }
                }
            }
        }
    });
}

function mockActiveExecutions(executions) {
    const ids = executions.map(e => e.id);

    axiosMock.onGet('executions/active').reply(200, ids);
    for (const execution of executions) {
        axiosMock.onGet('executions/config/' + execution.id).reply(200, execution);
    }
}

function mockStartResponse(id, status = 200) {
    axiosMock.onPost('executions/start').reply(status, id);
}

describe('Test scriptExecutionManager', function () {
    let store;

    beforeEach(async function () {
        store = createStore();
    });

    async function setupInitialExecutors(executions) {
        mockActiveExecutions(executions);
        await store.dispatch('executions/init');
        await flushPromises();
    }

    function assertExecution(id, expectedName, parameterValues) {
        const executor = store.state.executions.executors[id];
        expect(executor).not.toBeNil();
        expect(executor.state.scriptName).toBe(expectedName);
        expect(executor.state.parameterValues).toEqual(parameterValues);
    }

    function assertSelectedExecutor(expectedId) {
        const currentExecutor = store.state.executions.currentExecutor;

        if (isNull(expectedId)) {
            expect(currentExecutor).toBeNil();
        } else {
            expect(currentExecutor).not.toBeNil();
            expect(currentExecutor.state.id).toBe(expectedId);

            expect(store.state.scriptSetup.parameterValues).toEqual(currentExecutor.state.parameterValues);
        }
    }

    describe('Test init', function () {
        it('Test load executors', async function () {
            const executions = [
                {id: 123, scriptName: 'abc', parameterValues: {'p1': 1}},
                {id: 456, scriptName: 'def', parameterValues: {'p1': 1}},
                {id: 789, scriptName: 'abc', parameterValues: null}
            ];
            mockActiveExecutions(executions);

            await store.dispatch('executions/init');

            await flushPromises();

            for (const execution of executions) {
                assertExecution(execution.id, execution.scriptName, execution.parameterValues);
            }
            assertSelectedExecutor(null);
        });

        it('Test load executors check selectedExecutor from multiple', async function () {
            store.state.scripts.selectedScript = 'abc';

            const executions = [{id: 123, scriptName: 'def', parameterValues: {'p1': 1}},
                {id: 555, scriptName: 'abc', parameterValues: {'p1': 1}},
                {id: 444, scriptName: 'abc', parameterValues: null},
                {id: 666, scriptName: 'abc', parameterValues: null}
            ];
            mockActiveExecutions(executions);

            await store.dispatch('executions/init');

            await flushPromises();

            assertSelectedExecutor(444);
        });

        it('Test load executor check selectedExecutor when another selected', async function () {
            store.state.scripts.selectedScript = 'abc';

            mockStartResponse(12);
            await store.dispatch('executions/startExecution');
            await flushPromises();

            expect(store.state.executions.currentExecutor).not.toBeNil();
            expect(store.state.executions.currentExecutor.state.id).toBe(12);

            const executions = [{id: 555, scriptName: 'abc', parameterValues: {'p1': 1}}];
            mockActiveExecutions(executions);

            await store.dispatch('executions/init');
            await flushPromises();

            assertSelectedExecutor(12);
        });

        it('Test startExecution twice, when first is error', async function () {
            store.state.scripts.selectedScript = 'abc';

            mockStartResponse(null, 500);

            await store.dispatch('executions/startExecution');
            await flushPromises();

            const currentExecutor = store.state.executions.currentExecutor;
            expect(currentExecutor).not.toBeNil();
            expect(currentExecutor.state.id).toBeNil();
            expect(currentExecutor.state.scriptName).toEqual('abc');

            mockStartResponse(123);

            await store.dispatch('executions/startExecution');
            await flushPromises();

            assertSelectedExecutor(123);
        });
    });

    describe('Test selectExecutor', function () {

        async function selectExecutor(id) {
            const executor = store.state.executions.executors[id];
            await store.dispatch('executions/selectExecutor', executor);
        }

        it('Test selectExecutor', async function () {
            await setupInitialExecutors([{id: 123, scriptName: 'abc', parameterValues: {'p1': 1}}])
            await selectExecutor(123);

            assertSelectedExecutor(123);
        });

        it('Test selectExecutor when another selected', async function () {
            store.state.scripts.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc', parameterValues: {'p1': 1}},
                {id: 456, scriptName: 'def', parameterValues: {'p2': 'hello'}}])
            await selectExecutor(456);

            assertSelectedExecutor(456);
        });

        it('Test selectExecutor null', async function () {
            store.state.scripts.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])
            await selectExecutor(null);

            assertSelectedExecutor(null);
        });

        it('Test selectExecutor check remove current if finished', async function () {
            store.state.scripts.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])

            store.dispatch('executions/123/setFinished')

            await selectExecutor(456);

            expect(store.state.executions.executors[123]).toBeNil();
            expect(store.state.executions[123]).toBeNil();
        });

        it('Test selectExecutor when the same', async function () {
            store.state.scripts.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])

            store.dispatch('executions/123/setFinished')

            await selectExecutor(123);

            expect(store.state.executions.executors[123]).not.toBeNil();
            expect(store.state.executions[123]).not.toBeNil();
            assertSelectedExecutor(123);
        });
    });

    describe('Test selectScript', function () {

        async function selectScript(name) {
            await store.dispatch('executions/selectScript', {selectedScript: name});
        }

        it('Test selectScript when no executors', async function () {
            await selectScript('abc');

            assertSelectedExecutor(null);
        });

        it('Test selectScript when one executor with the same name', async function () {
            await setupInitialExecutors([{id: 123, scriptName: 'abc'}])
            await selectScript('abc');

            assertSelectedExecutor(123);
        });

        it('Test selectScript when one executor with another name', async function () {
            await setupInitialExecutors([{id: 123, scriptName: 'DEF'}])
            await selectScript('abc');

            assertSelectedExecutor(null);
        });

        it('Test selectScript when multiple executors with different names', async function () {
            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'DEF'},
                {id: 789, scriptName: 'xyz'}])

            await selectScript('DEF');

            assertSelectedExecutor(456);
        });

        it('Test selectScript when multiple executors with the same name', async function () {
            await setupInitialExecutors([
                {id: "10", scriptName: 'abc'},
                {id: "2", scriptName: 'abc'},
                {id: "9", scriptName: 'abc'}])

            await selectScript('abc');

            assertSelectedExecutor("2");
        });
    });

});


function createMockExecutor(id, scriptName, parameterValues) {
    return {
        namespaced: true,
        state: {
            id: id,
            parameterValues: parameterValues,
            status: STATUS_INITIALIZING,
            scriptName: scriptName
        },
        actions: {
            start({state, commit}, executionId) {
                commit('SET_STARTED', executionId)
            },
            setFinished({state}) {
                state.status = 'finished';
            }
        },
        mutations: {
            SET_STARTED(state, executionId) {
                state.id = executionId
                state.status = 'executing';
            }
        }
    };
}
