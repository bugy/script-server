import {clearArray, SocketClosedError} from '@/common/utils/common';
import {createPinia, setActivePinia} from 'pinia';
import {createScriptServerTestVue, timeout, vueTicks} from './test_utils'

// Vitest replacement for babel-plugin-rewire: scriptConfig imports ReactiveWebSocket
// from rxWebsocket. Mock it with a fake socket that records observers and sent data.
// reconnectionDelay is no longer overridden: the first reconnect is scheduled at
// (attempt-1)*delay = 0ms, so a single disconnect reconnects immediately under real timers.
const socketMock = vi.hoisted(() => {
    const observers = [];
    const sentData = [];

    function ReactiveWebSocket(path, callback) {
        const observer = {callback, path};
        observers.push(observer);
        let closed = false;

        this.close = () => {
            const i = observers.indexOf(observer);
            if (i >= 0) observers.splice(i, 1);
            closed = true;
        };
        this.send = (data) => sentData.push(data);
        this.isClosed = () => closed;
        this.isOpen = () => !closed;
    }

    return {observers, sentData, ReactiveWebSocket};
});

vi.mock('@/common/connections/rxWebsocket', async (importActual) => ({
    ...(await importActual()),
    ReactiveWebSocket: socketMock.ReactiveWebSocket
}));

import {useScriptConfigStore} from '@/main-app/stores/scriptConfig';
import {useScriptsStore} from '@/main-app/stores/scripts';

const DEFAULT_SCRIPT_NAME = 'testScript'

const DEFAULT_PARAM2_VALUES = ['abc', 'def', 'xyz'];

function createConfig(extraParameters = []) {

    const parameters = [{
        name: 'param1',
        'default': 123
    },
        {
            name: 'param2',
            type: 'list',
            values: DEFAULT_PARAM2_VALUES,
            'default': 'def'
        },
        ...extraParameters];

    return {
        name: DEFAULT_SCRIPT_NAME,
        description: 'some script description',
        parameters: parameters
    };
}

function createConfigEvent(config) {
    return JSON.stringify({
        event: 'initialConfig',
        data: config
    });
}

function createReloadModelEvent(config) {
    return JSON.stringify({
        event: 'reloadedConfig',
        data: config
    });
}

function createReloadModelRequest(clientModelId, parameterValues) {
    return JSON.stringify({
        event: 'reloadModelValues',
        data: {parameterValues, clientModelId}
    });
}

function createAddParameterEvent(parameter) {
    return JSON.stringify({
        event: 'parameterAdded',
        data: parameter
    });
}

function createUpdateParameterEvent(parameter, clientStateVersion) {
    return JSON.stringify({
        event: 'parameterChanged',
        data: {clientStateVersion, ...parameter}
    });
}

function createRemoveParameterEvent(parameter, clientStateVersion) {
    return JSON.stringify({
        event: 'parameterRemoved',
        data: {'parameterName': parameter, clientStateVersion}
    });
}

function createSentValueEvent(parameter, value, clientStateVersion) {
    return JSON.stringify({
        'event': 'parameterValue',
        data: {parameter, value, clientStateVersion}
    });
}

function createInitialValuesEvent(parameterValues) {
    return JSON.stringify({
        'event': 'initialValues',
        data: {parameterValues}
    });
}

function createClientStateVersionAcceptedEvent(clientStateVersion) {
    return JSON.stringify({
        event: 'clientStateVersionAccepted',
        data: {clientStateVersion}
    });
}

describe('Test scriptConfig module', function () {
    const observers = socketMock.observers;
    const sentData = socketMock.sentData;
    let store;
    let scriptsStore;

    beforeEach(function () {
        observers.length = 0;
        sentData.length = 0;

        setActivePinia(createPinia());
        store = useScriptConfigStore();
        scriptsStore = useScriptsStore();
        scriptsStore.selectedScript = DEFAULT_SCRIPT_NAME;
    });

    async function disconnectSocket(awaitTimeout) {
        const observer = observers[0];
        observers.splice(0, 1);
        observer.callback.onError(new SocketClosedError());
        await timeout(awaitTimeout);
    }

    function sendEventFromServer(event) {
        observers[0].callback.onNext(event)
    }

    function sendSocketError(error) {
        observers[0].callback.onError(error)
    }

    describe('Test config in single connection', function () {
        it('Test connect on reload', function () {
            store.reloadScript('my script');

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            expect(store.scriptConfig).toEqual(config);
            expect(store.parameters).toEqual(config.parameters);
            expect(store.preloadScript).toBeNil()
            expect(observers[0].path).toEndWith('?initWithValues=false')
        });

        it('Test replace config', function () {
            store.reloadScript('my script');

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            config.name = 'new name';
            config.parameters.splice(1, 1);
            config.parameters.push({name: 'param3'});

            sendEventFromServer(createConfigEvent(config));

            expect(store.scriptConfig).toEqual(config);
            expect(store.parameters).toEqual(config.parameters);
        });

        it('Test add parameter', function () {
            store.reloadScript('my script');

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            const newParameter = {name: 'param3', type: 'multiselect', 'default': 'abc'};

            sendEventFromServer(createAddParameterEvent(newParameter));

            const expectedParameters = config.parameters.concat([newParameter]);
            newParameter.multiselect = true;

            expect(store.parameters).toEqual(expectedParameters)
        });

        it('Test remove parameter', function () {
            store.reloadScript('my script');

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            sendEventFromServer(createRemoveParameterEvent(config.parameters[0].name, 1));

            config.parameters.splice(0, 1);

            expect(store.parameters).toEqual(config.parameters)
        });

        it('Test preload script', function () {
            store.reloadScript('my script');

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            let preloadScript = {
                'output': '123',
                'format': 'terminal'
            };
            sendEventFromServer(JSON.stringify({
                event: 'preloadScript',
                data: preloadScript
            }));

            expect(store.preloadScript).toEqual(preloadScript)
        });
    });

    describe('Test reconnection', function () {
        it('Test disconnect before initial config', function () {
            store.reloadScript('my script');

            sendSocketError(new SocketClosedError());

            expect(store.scriptConfig).toBeNil()
            expect(store.loadError).toBe('Failed to connect to the server')
        });

        it('Test disconnect after initial config', async function () {
            store.reloadScript('my script');

            const oldObserver = observers[0];

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await disconnectSocket(50);

            const newObserver = observers[0];

            expect(newObserver).not.toEqual(oldObserver)
            expect(store.scriptConfig).toEqual(config)
            expect(store.loadError).toBeNil()
        });

        it('Test reload config after reconnect', async function () {
            store.reloadScript('my script');

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await disconnectSocket(50);

            expect(store.scriptConfig).toEqual(config)
            config.name = 'new name';
            config.parameters.push({'name': 'param3'});

            sendEventFromServer(createConfigEvent(config));

            expect(store.scriptConfig).toEqual(config)
            expect(store.parameters).toEqual(config.parameters)
        });
    });

    describe('Test send current value', function () {
        it('Test send value', function () {
            store.reloadScript('my script');

            store.sendParameterValue({parameterName: 'param1', value: 123});

            expect(sentData).toEqual([createSentValueEvent('param1', 123, 1)])
        });

        it('Test send same value multiple times', function () {
            store.reloadScript('my script');

            store.sendParameterValue({parameterName: 'param1', value: 123});
            store.sendParameterValue({parameterName: 'param1', value: 123});
            store.sendParameterValue({parameterName: 'param1', value: 123});

            expect(sentData).toEqual([createSentValueEvent('param1', 123, 1)])
        });

        it('Test send same parameter different values', function () {
            store.reloadScript('my script');

            store.sendParameterValue({parameterName: 'param1', value: 123});
            store.sendParameterValue({parameterName: 'param1', value: 456});
            store.sendParameterValue({parameterName: 'param1', value: 123});

            expect(sentData).toEqual([
                createSentValueEvent('param1', 123, 1),
                createSentValueEvent('param1', 456, 2),
                createSentValueEvent('param1', 123, 3)
            ])
        });

        it('Test send different parameters', function () {
            store.reloadScript('my script');

            store.sendParameterValue({parameterName: 'param2', value: 123});
            store.sendParameterValue({parameterName: 'param1', value: 'hello'});

            expect(sentData).toEqual([
                createSentValueEvent('param2', 123, 1),
                createSentValueEvent('param1', 'hello', 2)
            ])
        });

        it('Test resend values on reconnect', async function () {
            store.reloadScript('my script');

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            store.sendParameterValue({parameterName: 'param2', value: 123});
            store.sendParameterValue({parameterName: 'param1', value: 'hello'});

            clearArray(sentData);

            await disconnectSocket(100);

            expect(sentData).toEqual(
                [createInitialValuesEvent({param2: 123, param1: 'hello'})])
            expect(observers[0].path).toEndWith('?initWithValues=true')

            clearArray(sentData);

            sendEventFromServer(createConfigEvent(config));

            expect(sentData).toEqual([
                createSentValueEvent('param2', 123),
                createSentValueEvent('param1', 'hello')
            ])
        });
    });

    describe('Test reloadModel', function () {
        beforeEach(function () {
            store.reloadScript(DEFAULT_SCRIPT_NAME);
            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));
        })

        it('Test simple scenario', async function () {
            const parameterValues = {'param1': 'abc'}
            const modelId = 12345

            store.reloadModel(
                {parameterValues: parameterValues, clientModelId: modelId, scriptName: DEFAULT_SCRIPT_NAME});

            expect(sentData).toEqual([createReloadModelRequest(modelId, parameterValues)])
            expect(store.loading).toBeTrue()

            clearArray(sentData)

            const newConfig = createConfig()
            newConfig.name = 'New name'
            newConfig.clientModelId = modelId

            sendEventFromServer(createReloadModelEvent(newConfig))

            expect(store.loading).toBeFalse()
            expect(store.scriptConfig).toEqual(newConfig)
            expect(sentData).toBeEmpty()
        })

        it('Test ignore reload for different script', async function () {
            scriptsStore.selectedScript = 'another script'

            store.reloadModel(
                {
                    parameterValues: {'param1': 'abc'},
                    clientModelId: 12345,
                    scriptName: DEFAULT_SCRIPT_NAME
                });

            expect(sentData).toEqual([])
            expect(store.loading).toBeFalse()
        })
    })

    describe('Test reload dependant parameter', function () {
        beforeEach(async function () {
            store.reloadScript('my script');

            const config = createConfig([{
                name: 'dependant param',
                type: 'list',
                values: DEFAULT_PARAM2_VALUES,
                'default': 'def',
                'requiredParameters': ['param1']
            }])

            sendEventFromServer(createConfigEvent(config));
            await vueTicks()
        })

        function assertLoading(paramName, expectedValue) {
            const dependantParam = store.parameters.find(p => p.name === paramName)
            expect(dependantParam.loading || false).toEqual(expectedValue)
        }

        async function prepareMultiDependantConfig() {
            const config = createConfig([{
                name: 'p1',
                type: 'list',
                values: [1, 2, 3],
                'requiredParameters': ['param1']
            }, {
                name: 'p2',
                type: 'list',
                values: [9, 8, 7],
                'requiredParameters': ['param1']
            }])

            sendEventFromServer(createConfigEvent(config));
            await vueTicks()

            store.sendParameterValue({
                parameterName: 'param1',
                value: 1
            });
            await vueTicks()

            assertLoading('p1', true)
            assertLoading('p2', true)
        }

        it('test set parameter to loading on dependency change', async function () {
            store.sendParameterValue({parameterName: 'param1', value: 123});
            await vueTicks()

            assertLoading('param1', false)
            assertLoading('param2', false)
            assertLoading('dependant param', true)
        })

        it('test reset loading getting server event', async function () {
            store.sendParameterValue({parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createUpdateParameterEvent({name: 'dependant param', default: 'xyz'}, 3));
            await vueTicks()

            assertLoading('dependant param', false)
            const dependantParam = store.parameters.find(p => p.name === 'dependant param')
            expect(dependantParam.default).toEqual('xyz')
        })

        it('test keep loading on old event', async function () {
            store.sendParameterValue({parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createUpdateParameterEvent({name: 'dependant param', default: 'xyz'}, 0));
            await vueTicks()

            assertLoading('dependant param', true)

            const dependantParam = store.parameters.find(p => p.name === 'dependant param')
            expect(dependantParam.default).toEqual('xyz')
        })

        it('test reset loading on clientStateVersionAccepted', async function () {
            store.sendParameterValue({parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createClientStateVersionAcceptedEvent(3));
            await vueTicks()

            assertLoading('dependant param', false)
        })

        it('test no loading when not dependency change', async function () {
            store.sendParameterValue({
                parameterName: 'param2',
                value: DEFAULT_PARAM2_VALUES[1]
            });
            await vueTicks()

            assertLoading('param1', false)
            assertLoading('param2', false)
            assertLoading('dependant param', false)
        })

        it('test no loading when multiple dependant parameters, clientStateVersionAccepted', async function () {
            await prepareMultiDependantConfig()

            sendEventFromServer(createClientStateVersionAcceptedEvent(3));
            await vueTicks()

            assertLoading('p1', false)
            assertLoading('p2', false)
        })

        it('test no loading when multiple dependant parameters, parameterChanged', async function () {
            await prepareMultiDependantConfig()

            sendEventFromServer(createUpdateParameterEvent({name: 'p2', default: 'xyz'}, 3));
            await vueTicks()

            assertLoading('p1', true)
            assertLoading('p2', false)
        })

        it('test no loading when multiple dependant parameters, parameterAdded', async function () {
            await prepareMultiDependantConfig()

            sendEventFromServer(createUpdateParameterEvent({name: 'p3', default: 'xyz'}, 3));
            await vueTicks()

            assertLoading('p1', true)
            assertLoading('p2', true)
        })
    })
});
