import scriptExecutor, {__RewireAPI__ as ExecutorRewireAPI} from '@/main-app/store/scriptExecutor';

import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import {assert} from 'chai';
import {Server, WebSocket} from 'mock-socket';
import * as sinon from 'sinon';
import Vuex from 'vuex';
import {createScriptServerTestVue, timeout} from './test_utils'

const axiosMock = new MockAdapter(axios);
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
        websocketServer = new Server('ws://localhost:9876/executions/io/123');
        websocketServer.on('connection', socket => {
            currentSocket = socket;
        });
    });
    afterEach(function () {
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

            assert.isTrue(spy.calledOnce);
            assert.equal('executing', store.state.scriptExecutor.status);
        });

        it('Test error status', async function () {
            await store.dispatch('scriptExecutor/setErrorStatus');

            assert.equal('error', store.state.scriptExecutor.status);
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

            assert.equal('finished', store.state.scriptExecutor.status);
        });

        it('Test socket closed on disconnect when finished', async function () {
            await mockSocketClose(1006, 'finished');

            assert.equal('finished', store.state.scriptExecutor.status);
        });

        it('Test socket closed on disconnect when executing', async function () {
            await mockSocketClose(1006, 'executing');

            assert.equal('disconnected', store.state.scriptExecutor.status);
        });

        it('Test socket closed on disconnect when get status error', async function () {
            await mockSocketClose(1006, new Error('test message'));

            assert.equal('error', store.state.scriptExecutor.status);
        });
    });

    describe('Test kill enabling', function () {
        let store;

        beforeEach(async function () {
            store = createStore();

            await store.dispatch('scriptExecutor/reconnect');
        });

        it('Test kill fields default', async function () {
            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields immediately after stop', async function () {
            await store.dispatch('scriptExecutor/stopExecution');

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.equal(5, store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after short timeout', async function () {
            ExecutorRewireAPI.__Rewire__('oneSecDelay', 50);

            await store.dispatch('scriptExecutor/stopExecution');
            await timeout(75);

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.equal(4, store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after long timeout', async function () {
            ExecutorRewireAPI.__Rewire__('oneSecDelay', 5);

            await store.dispatch('scriptExecutor/stopExecution');
            await timeout(50);

            assert.isTrue(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after error', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await store.dispatch('scriptExecutor/setErrorStatus');

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after socket closed on finish', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1000, 'finished');

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after socket closed on disconnect and executing', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1006, 'executing');

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });

        it('Test kill fields after socket closed on disconnect and finished', async function () {
            await store.dispatch('scriptExecutor/stopExecution');
            await mockSocketClose(1006, 'finished');

            assert.isFalse(store.state.scriptExecutor.killEnabled);
            assert.isNull(store.state.scriptExecutor.killTimeoutSec);
        });
    });
});