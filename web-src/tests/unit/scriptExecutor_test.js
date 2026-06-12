import {createExecutor} from '@/main-app/stores/scriptExecutor';

import {axiosInstance} from '@/common/utils/axios_utils';
import MockAdapter from 'axios-mock-adapter';
import {Server, WebSocket} from 'mock-socket';
import * as sinon from 'sinon';
import {createScriptServerTestVue, timeout} from './test_utils'

let axiosMock;

window.WebSocket = WebSocket;

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
    let executor;

    beforeEach(function () {
        axiosMock = new MockAdapter(axiosInstance)

        // The executor builds its socket URL from window.location.host (via
        // getWebsocketUrl), so match the mock server to the current jsdom host
        // rather than a hard-coded port.
        websocketServer = new Server(`ws://${window.location.host}/executions/io/123`);
        websocketServer.on('connection', socket => {
            currentSocket = socket;
        });

        executor = createExecutor(123, 'my script', {});
    });
    afterEach(function () {
        axiosMock.restore()
        websocketServer.stop();
    });

    async function mockSocketClose(socketCloseCode, status) {
        await timeout(20);
        mockExecutionStatus(123, status);
        currentSocket.close({code: socketCloseCode});
        await timeout(20);
    }

    describe('Test basic features', function () {

        beforeEach(async function () {
            await executor.reconnect();
        });

        it('Test stop script', async function () {
            const spy = mockStopEndpoint(123);

            await executor.stopExecution();

            expect(spy.calledOnce).toBeTrue()
            expect(executor.state.status).toBe('executing')
        });

        it('Test error status', async function () {
            executor.setErrorStatus();

            expect(executor.state.status).toBe('error')
        });
    });

    describe('Test socket disconnect', function () {

        beforeEach(async function () {
            await executor.reconnect();
        });

        it('Test socket closed on finish', async function () {
            await mockSocketClose(1000, 'xyz');

            expect(executor.state.status).toBe('finished')
        });

        it('Test socket closed on disconnect when finished', async function () {
            await mockSocketClose(1006, 'finished');

            expect(executor.state.status).toBe('finished')
        });

        it('Test socket closed on disconnect when executing', async function () {
            await mockSocketClose(1006, 'executing');

            expect(executor.state.status).toBe('disconnected')
        });

        it('Test socket closed on disconnect when get status error', async function () {
            await mockSocketClose(1006, new Error('test message'));

            expect(executor.state.status).toBe('error')
        });
    });

    describe('Test kill enabling', function () {

        beforeEach(async function () {
            mockStopEndpoint(123);
            await executor.reconnect();
        });

        it('Test kill fields default', async function () {
            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBeNil()
        });

        it('Test kill fields immediately after stop', async function () {
            await executor.stopExecution();

            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBe(5)
        });

        // The kill countdown uses setInterval(..., oneSecDelay) with oneSecDelay = 1000.
        // babel-plugin-rewire shrank that const to run fast; under Vitest we keep the
        // real value and drive the interval with fake timers instead.
        it('Test kill fields after short timeout', async function () {
            vi.useFakeTimers();
            try {
                await executor.stopExecution();
                await vi.advanceTimersByTimeAsync(1000); // one tick

                expect(executor.state.killEnabled).toBeFalse()
                expect(executor.state.killTimeoutSec).toBe(4)
            } finally {
                vi.useRealTimers();
            }
        });

        it('Test kill fields after long timeout', async function () {
            vi.useFakeTimers();
            try {
                await executor.stopExecution();
                await vi.advanceTimersByTimeAsync(5000); // five ticks -> countdown reaches 0

                expect(executor.state.killEnabled).toBeTrue()
                expect(executor.state.killTimeoutSec).toBeNil()
            } finally {
                vi.useRealTimers();
            }
        });

        it('Test kill fields after error', async function () {
            await executor.stopExecution();
            executor.setErrorStatus();

            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on finish', async function () {
            await executor.stopExecution();
            await mockSocketClose(1000, 'finished');

            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on disconnect and executing', async function () {
            await executor.stopExecution();
            await mockSocketClose(1006, 'executing');

            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBeNil()
        });

        it('Test kill fields after socket closed on disconnect and finished', async function () {
            await executor.stopExecution();
            await mockSocketClose(1006, 'finished');

            expect(executor.state.killEnabled).toBeFalse()
            expect(executor.state.killTimeoutSec).toBeNil()
        });
    });
});
