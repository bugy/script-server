import {clearArray, removeElement, SocketClosedError} from '@/common/utils/common';
import scriptConfig, {__RewireAPI__ as SocketRewireAPI} from '@/main-app/store/scriptConfig';
import Vuex from 'vuex';
import {createScriptServerTestVue, timeout, vueTicks} from './test_utils'


const localVue = createScriptServerTestVue();
localVue.use(Vuex);

const DEFAULT_SCRIPT_NAME = 'testScript'

function createStore() {
    return new Vuex.Store({
        modules: {
            scriptConfig: scriptConfig(),
            scripts: {
                namespaced: true,
                state: {
                    selectedScript: DEFAULT_SCRIPT_NAME
                }
            }
        }
    });
}

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
    let observers = [];

    beforeEach(function () {
        const sentData = [];

        this.sentData = sentData;

        SocketRewireAPI.__Rewire__('ReactiveWebSocket', function (path, callback) {
            const observer = {callback, path}
            observers.push(observer);
            let closed = false;

            this.close = () => {
                removeElement(observers, observer);
                closed = true;
            };

            this.send = (data) => {
                sentData.push(data);
            };

            this.isClosed = () => closed;
            this.isOpen = () => !closed;
        });

        SocketRewireAPI.__Rewire__('reconnectionDelay', 10);

        this.disconnectSocket = async function (awaitTimeout) {
            const observer = observers[0];
            observers.splice(0, 1);
            observer.callback.onError(new SocketClosedError());
            await timeout(awaitTimeout);
        };
    });

    function sendEventFromServer(event) {
        observers[0].callback.onNext(event)
    }

    function sendSocketError(error) {
        observers[0].callback.onError(error)
    }

    describe('Test config in single connection', function () {
        it('Test connect on reload', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            expect(store.state.scriptConfig.scriptConfig).toEqual(config);
            expect(store.state.scriptConfig.parameters).toEqual(config.parameters);
            expect(store.state.scriptConfig.preloadScript).toBeNil()
            expect(observers[0].path).toEndWith('?initWithValues=false')
        });

        it('Test replace config', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            config.name = 'new name';
            config.parameters.splice(1, 1);
            config.parameters.push({name: 'param3'});

            sendEventFromServer(createConfigEvent(config));

            expect(store.state.scriptConfig.scriptConfig).toEqual(config);
            expect(store.state.scriptConfig.parameters).toEqual(config.parameters);
        });

        it('Test add parameter', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            const newParameter = {name: 'param3', type: 'multiselect', 'default': 'abc'};

            sendEventFromServer(createAddParameterEvent(newParameter));

            const expectedParameters = config.parameters.concat([newParameter]);
            newParameter.multiselect = true;

            expect(store.state.scriptConfig.parameters).toEqual(expectedParameters)
        });

        it('Test remove parameter', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            sendEventFromServer(createRemoveParameterEvent(config.parameters[0].name, 1));

            config.parameters.splice(0, 1);

            expect(store.state.scriptConfig.parameters).toEqual(config.parameters)
        });

        it('Test preload script', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

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

            expect(store.state.scriptConfig.preloadScript).toEqual(preloadScript)
        });
    });

    describe('Test reconnection', function () {
        it('Test disconnect before initial config', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];
            sendSocketError(new SocketClosedError());

            expect(store.state.scriptConfig.scriptConfig).toBeNil()
            expect(store.state.scriptConfig.loadError).toBe('Failed to connect to the server')
        });

        it('Test disconnect after initial config', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await this.disconnectSocket(50);

            const newObserver = observers[0];

            expect(newObserver).not.toEqual(oldObserver)
            expect(store.state.scriptConfig.scriptConfig).toEqual(config)
            expect(store.state.scriptConfig.loadError).toBeNil()
        });

        it('Test reload config after reconnect', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await this.disconnectSocket(50);

            expect(store.state.scriptConfig.scriptConfig).toEqual(config)
            config.name = 'new name';
            config.parameters.push({'name': 'param3'});

            sendEventFromServer(createConfigEvent(config));

            expect(store.state.scriptConfig.scriptConfig).toEqual(config)
            expect(store.state.scriptConfig.parameters).toEqual(config.parameters)
        });
    });

    describe('Test send current value', function () {
        it('Test send value', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            expect(this.sentData).toEqual([createSentValueEvent('param1', 123, 1)])
        });

        it('Test send same value multiple times', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            expect(this.sentData).toEqual([createSentValueEvent('param1', 123, 1)])
        });

        it('Test send same parameter different values', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 456});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            expect(this.sentData).toEqual([
                createSentValueEvent('param1', 123, 1),
                createSentValueEvent('param1', 456, 2),
                createSentValueEvent('param1', 123, 3)
            ])
        });

        it('Test send different parameters', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param2', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 'hello'});

            expect(this.sentData).toEqual([
                createSentValueEvent('param2', 123, 1),
                createSentValueEvent('param1', 'hello', 2)
            ])
        });

        it('Test resend values on reconnect', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param2', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 'hello'});

            clearArray(this.sentData);

            await this.disconnectSocket(100);

            expect(this.sentData).toEqual(
                [createInitialValuesEvent({param2: 123, param1: 'hello'})])
            expect(observers[0].path).toEndWith('?initWithValues=true')

            clearArray(this.sentData);

            sendEventFromServer(createConfigEvent(config));

            expect(this.sentData).toEqual([
                createSentValueEvent('param2', 123),
                createSentValueEvent('param1', 'hello')
            ])
        });
    });

    describe('Test reloadModel', function () {
        let store

        beforeEach(function () {
            store = createStore();

            store.dispatch('scriptConfig/reloadScript', {selectedScript: DEFAULT_SCRIPT_NAME});
            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));
        })

        it('Test simple scenario', async function () {
            const parameterValues = {'param1': 'abc'}
            const modelId = 12345

            store.dispatch('scriptConfig/reloadModel',
                {parameterValues: parameterValues, clientModelId: modelId, scriptName: DEFAULT_SCRIPT_NAME});

            expect(this.sentData).toEqual([createReloadModelRequest(modelId, parameterValues)])
            expect(store.state.scriptConfig.loading).toBeTrue()

            clearArray(this.sentData)

            const newConfig = createConfig()
            newConfig.name = 'New name'
            newConfig.clientModelId = modelId

            sendEventFromServer(createReloadModelEvent(newConfig))

            expect(store.state.scriptConfig.loading).toBeFalse()
            expect(store.state.scriptConfig.scriptConfig).toEqual(newConfig)
            expect(this.sentData).toBeEmpty()
        })

        it('Test ignore reload for different script', async function () {
            store.state.scripts.selectedScript = 'another script'

            store.dispatch('scriptConfig/reloadModel',
                {
                    parameterValues: {'param1': 'abc'},
                    clientModelId: 12345,
                    scriptName: DEFAULT_SCRIPT_NAME
                });

            expect(this.sentData).toEqual([])
            expect(store.state.scriptConfig.loading).toBeFalse()
        })
    })

    describe('Test reload dependant parameter', function () {
        let store

        beforeEach(async function () {
            store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

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
            const dependantParam = store.state.scriptConfig.parameters.find(p => p.name === paramName)
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

            store.dispatch('scriptConfig/sendParameterValue', {
                parameterName: 'param1',
                value: 1
            });
            await vueTicks()

            assertLoading('p1', true)
            assertLoading('p2', true)
        }

        it('test set parameter to loading on dependency change', async function () {
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            await vueTicks()

            assertLoading('param1', false)
            assertLoading('param2', false)
            assertLoading('dependant param', true)
        })

        it('test reset loading getting server event', async function () {
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createUpdateParameterEvent({name: 'dependant param', default: 'xyz'}, 3));
            await vueTicks()

            assertLoading('dependant param', false)
            const dependantParam = store.state.scriptConfig.parameters.find(p => p.name === 'dependant param')
            expect(dependantParam.default).toEqual('xyz')
        })

        it('test keep loading on old event', async function () {
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createUpdateParameterEvent({name: 'dependant param', default: 'xyz'}, 0));
            await vueTicks()

            assertLoading('dependant param', true)

            const dependantParam = store.state.scriptConfig.parameters.find(p => p.name === 'dependant param')
            expect(dependantParam.default).toEqual('xyz')
        })

        it('test reset loading on clientStateVersionAccepted', async function () {
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            await vueTicks()
            sendEventFromServer(createClientStateVersionAcceptedEvent(3));
            await vueTicks()

            assertLoading('dependant param', false)
        })

        it('test no loading when not dependency change', async function () {
            store.dispatch('scriptConfig/sendParameterValue', {
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