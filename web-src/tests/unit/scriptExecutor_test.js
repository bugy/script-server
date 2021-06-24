import scriptExecutor, {__RewireAPI__ as ExecutorRewireAPI} from '@/main-app/store/scriptExecutor';

import {axiosInstance} from '@/common/utils/axios_utils';
import MockAdapter from 'axios-mock-adapter';
import {Server, WebSocket} from 'mock-socket';
import * as sinon from 'sinon';
import Vuex from 'vuex';
import {createScriptServerTestVue, timeout} from './test_utils'

let axiosMock;

window.WebSocket = WebSocket;

const localVue = createScriptServerTestVue();
localVue.use(Vuex);

function createStore() {
    return new Vuex.Store({
        modules: {
            scriptExecutor: scriptExecutor(123, 'my script', {})
        }
    });
}

function mockStopEndpoint(id) {
    const spy = sinon.spy(function () {
        return [200];
    });
    axiosMock.onPost('executions/stop/' + id).reply(spy);
    return spy;
}

function mockExecutionStatus(id, status) {
    const spy = sinon.spy(function () {
        if (status instanceof Error) {
            return [500, status.message];
        } else {
            return [200, status];
        }
    });
    axiosMock.onGet('executions/status/' + id).reply(spy);
    return spy;
}

describe('Test scriptExecutor module', function () {
    let currentSocket = null;
    let websocketServer = null;

    beforeEach(function () {
        axiosMock = new MockAdapter(axiosInstance)

        websocketServer = new Server('ws://localhost:9876/executions/io/123');
        websocketServer.on('connection', socket => {
            currentSocket = socket;
        });
    });
    afterEach(function () {
        axiosMock.restore()
        websocketServer.stop();

        ExecutorRewireAPI.__ResetDependency__('oneSecDelay', 1000);
    });

    async function mockSocketClose(socketCloseCode, status) {
        await timeout(20);
        mockExecutionStatus(123, status);
        currentSocket.close({code: socketCloseCode});
        await timeout(20);
    }

    describe('Test basic features', function () {
        let store;

        beforeEach(async function () {
            store = createStore();

            await store.dispatch('scriptExecutor/reconnect');
        });

        it('Test stop script', async function () {
            const spy = mockStopEndpoint(123);

            await store.dispatch('scriptExecutor/stopExecution');

            expect(spy.calledOnce).toBeTrue()
            expect(store.state.scriptExecutor.status).toBe('executing')
        });

        it('Test error status', async function () {
            await store.dispatch('scriptExecutor/setErrorStatus');

            expect(store.state.scriptExecutor.status).toBe('error')
        });
    });

    describe('Test socket disconnect', function () {
        let store;

        beforeEach(async function () {
            store = createStore();

            await store.dispatch('scriptExecutor/reconnect');
        });

        it('Test socket closed on finish', async function () {
            await mockSocketClose(1000, 'xyz');

            expect(store.state.scriptExecutor.status).toBe('finished')
        });

        it('Test socket closed on disconnect when finished', async function () {
            await mockSocketClose(1006, 'finished');

            expect(store.state.scriptExecutor.status).toBe('finished')
        });

        it('Test socket closed on disconnect when executing', async function () {
            await mockSocketClose(1006, 'executing');

            expect(store.state.scriptExecutor.status).toBe('disconnected')
        });

        it('Test socket closed on disconnect when get status error', async function () {
            await mockSocketClose(1006, new Error('test message'));

            expect(store.state.scriptExecutor.status).toBe('error')
        });
    });

    describe('Test kill enabling', function () {
        let store;

        beforeEach(async function () {
            store = createStore();

            mockStopEndpoint(123);
            await store.dispatch('scriptExecutor/reconnect');
        });

        it('Test kill fields default', async function () {
            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });

        it('Test kill fields immediately after stop', async function () {
            await store.dispatch('scriptExecutor/stopExecution');

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBe(5)
        });

        it('Test kill fields after short timeout', async function () {
            ExecutorRewireAPI.__Rewire__('oneSecDelay', 50);

            await store.dispatch('scriptExecutor/stopExecution');
            await timeout(75);

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBe(4)
        });

        it('Test kill fields after long timeout', async function () {
            ExecutorRewireAPI.__Rewire__('oneSecDelay', 5);

            await store.dispatch('scriptExecutor/stopExecution');
            await timeout(50);

            expect(store.state.scriptExecutor.killEnabled).toBeTrue()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after error', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await store.dispatch('scriptExecutor/setErrorStatus');

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on finish', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1000, 'finished');

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on disconnect and executing', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1006, 'executing');

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on disconnect and finished', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1006, 'finished');

            expect(store.state.scriptExecutor.killEnabled).toBeFalse()
            expect(store.state.scriptExecutor.killTimeoutSec).toBeNil()
        });
    });
});