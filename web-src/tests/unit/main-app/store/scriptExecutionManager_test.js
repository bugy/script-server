import {isNull} from '@/common/utils/common';
import {axiosInstance} from '@/common/utils/axios_utils';
import MockAdapter from 'axios-mock-adapter';
import {WebSocket} from 'mock-socket';
import {createPinia, setActivePinia} from 'pinia';
import {reactive} from 'vue';
import {createScriptServerTestVue, flushPromises, timeout} from '../../test_utils';

// Mock createExecutor — returns a lightweight reactive executor matching the
// interface that useExecutionsStore expects (state.xxx + reconnect/start methods).
const {createMockExecutor} = vi.hoisted(() => {
    const STATUS_INITIALIZING = 'initializing';

    function createMockExecutor(id, scriptName, parameterValues) {
        const executor = reactive({
            state: {
                id,
                parameterValues,
                status: STATUS_INITIALIZING,
                scriptName
            },
            reconnect() {},
            start(executionId) {
                executor.state.id = executionId;
                executor.state.status = 'executing';
            },
            setInitialising() {
                executor.state.logChunks = ['Calling the script...'];
                executor.state.status = STATUS_INITIALIZING;
            },
            setErrorStatus() {
                executor.state.status = 'error';
            },
            setFinished() {
                executor.state.status = 'finished';
            },
            appendLog() {},
            abort() {
                return Promise.resolve();
            }
        });
        return executor;
    }

    return {createMockExecutor};
});

vi.mock('@/main-app/stores/scriptExecutor', async (importActual) => ({
    ...(await importActual()),
    createExecutor: createMockExecutor
}));

import {useExecutionsStore} from '@/main-app/stores/executions';
import {useScriptsStore} from '@/main-app/stores/scripts';
import {useScriptSetupStore} from '@/main-app/stores/scriptSetup';
import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';

let axiosMock;
window.WebSocket = WebSocket;

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
    let scriptsStore;
    let scriptSetupStore;
    let parameterValues;

    beforeEach(async function () {
        parameterValues = {};
        setActivePinia(createPinia());

        store = useExecutionsStore();
        scriptsStore = useScriptsStore();

        // Spy on scriptSetup to track reloadModel calls and capture parameterValues
        scriptSetupStore = useScriptSetupStore();
        vi.spyOn(scriptSetupStore, 'reloadModel').mockImplementation(({values}) => {
            parameterValues = values;
        });
        Object.defineProperty(scriptSetupStore, 'parameterValues', {
            get: () => parameterValues,
            configurable: true
        });

        // Stub scriptConfig to prevent websocket side-effects
        const scriptConfig = useScriptConfigStore();
        vi.spyOn(scriptConfig, 'reloadModel').mockImplementation(() => {});
        vi.spyOn(scriptConfig, 'sendParameterValue').mockImplementation(() => {});
        // Stub reloadScript to prevent websocket creation
        vi.spyOn(scriptConfig, 'reloadScript').mockImplementation(() => {});
        // Provide scriptConfig.scriptConfig for startExecution
        scriptConfig.scriptConfig = {name: 'abc'};

        axiosMock = new MockAdapter(axiosInstance)
    });

    afterEach(function () {
        vi.restoreAllMocks();
        axiosMock.restore()
    })

    async function setupInitialExecutors(executions) {
        mockActiveExecutions(executions);
        await store.init();
        await flushPromises();
        await timeout(10)
    }

    function assertExecution(id, expectedName, expectedParamValues) {
        const executor = store.executors[id];
        expect(executor).not.toBeNil();
        expect(executor.state.scriptName).toBe(expectedName);
        expect(executor.state.parameterValues).toEqual(expectedParamValues);
    }

    function assertSelectedExecutor(expectedId) {
        const currentExecutor = store.currentExecutor;

        if (isNull(expectedId)) {
            expect(currentExecutor).toBeNil();
        } else {
            expect(currentExecutor).not.toBeNil();
            expect(currentExecutor.state.id).toBe(expectedId);

            expect(parameterValues).toEqual(currentExecutor.state.parameterValues);
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

            await store.init();

            await flushPromises();

            for (const execution of executions) {
                assertExecution(execution.id, execution.scriptName, execution.parameterValues);
            }
            assertSelectedExecutor(null);
        });

        it('Test load executors check selectedExecutor from multiple', async function () {
            scriptsStore.selectedScript = 'abc';

            const executions = [{id: 123, scriptName: 'def', parameterValues: {'p1': 1}},
                {id: 555, scriptName: 'abc', parameterValues: {'p1': 1}},
                {id: 444, scriptName: 'abc', parameterValues: null},
                {id: 666, scriptName: 'abc', parameterValues: null}
            ];
            mockActiveExecutions(executions);

            await store.init();

            await flushPromises();

            assertSelectedExecutor(444);
        });

        it('Test load executor check selectedExecutor when another selected', async function () {
            scriptsStore.selectedScript = 'abc';

            mockStartResponse(12);
            await store.startExecution();
            await flushPromises();

            expect(store.currentExecutor).not.toBeNil();
            expect(store.currentExecutor.state.id).toBe(12);

            const executions = [{id: 555, scriptName: 'abc', parameterValues: {'p1': 1}}];
            mockActiveExecutions(executions);

            await store.init();
            await flushPromises();

            assertSelectedExecutor(12);
        });

        it('Test startExecution twice, when first is error', async function () {
            scriptsStore.selectedScript = 'abc';

            mockStartResponse(null, 500);

            await store.startExecution();
            await flushPromises();

            const currentExecutor = store.currentExecutor;
            expect(currentExecutor).not.toBeNil();
            expect(currentExecutor.state.id).toBeNil();
            expect(currentExecutor.state.scriptName).toEqual('abc');

            mockStartResponse(123);

            await store.startExecution();
            await flushPromises();

            assertSelectedExecutor(123);
        });
    });

    describe('Test selectExecutor', function () {

        async function selectExecutor(id) {
            const executor = store.executors[id];
            await store.selectExecutor(executor);
        }

        it('Test selectExecutor', async function () {
            await setupInitialExecutors([{id: 123, scriptName: 'abc', parameterValues: {'p1': 1}}])
            await selectExecutor(123);

            assertSelectedExecutor(123);
        });

        it('Test selectExecutor when another selected', async function () {
            scriptsStore.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc', parameterValues: {'p1': 1}},
                {id: 456, scriptName: 'def', parameterValues: {'p2': 'hello'}}])
            await selectExecutor(456);

            assertSelectedExecutor(456);
        });

        it('Test selectExecutor null', async function () {
            scriptsStore.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])
            await selectExecutor(null);

            assertSelectedExecutor(null);
        });

        it('Test selectExecutor check remove current if finished', async function () {
            scriptsStore.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])

            store.executors[123].setFinished()

            await selectExecutor(456);

            expect(store.executors[123]).toBeNil();
        });

        it('Test selectExecutor when the same', async function () {
            scriptsStore.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])

            store.executors[123].setFinished()

            await selectExecutor(123);

            expect(store.executors[123]).not.toBeNil();
            assertSelectedExecutor(123);
        });

        it('Test selectExecutor check remove current if error', async function () {
            scriptsStore.selectedScript = 'abc';

            await setupInitialExecutors([
                {id: 123, scriptName: 'abc'},
                {id: 456, scriptName: 'def'}])

            store.executors[123].setErrorStatus()

            await selectExecutor(456);

            expect(store.executors[123]).toBeNil();
        });


    });

    describe('Test selectScript', function () {

        async function selectScript(name) {
            await store.selectScript({selectedScript: name});
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
