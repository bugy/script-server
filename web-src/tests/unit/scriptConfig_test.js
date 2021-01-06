import {clearArray, removeElement, SocketClosedError} from '@/common/utils/common';
import scriptConfig, {__RewireAPI__ as SocketRewireAPI} from '@/main-app/store/scriptConfig';
import {assert} from 'chai';
import Vuex from 'vuex';
import {createScriptServerTestVue, timeout} from './test_utils'


const localVue = createScriptServerTestVue();
localVue.use(Vuex);

const DEFAULT_SCRIPT_NAME = 'testScript'

function createStore() {
    return new Vuex.Store({
        modules: {
            scriptConfig: scriptConfig,
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

function createConfig() {

    const parameters = [{
        name: 'param1',
        'default': 123
    },
        {
            name: 'param2',
            type: 'list',
            values: DEFAULT_PARAM2_VALUES,
            'default': 'def'
        }];

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

function createUpdateParameterEvent(parameter) {
    return JSON.stringify({
        event: 'parameterChanged',
        data: parameter
    });
}

function createRemoveParameterEvent(parameter) {
    return JSON.stringify({
        event: 'parameterRemoved',
        data: parameter
    });
}

function createSentValueEvent(parameter, value) {
    return JSON.stringify({
        'event': 'parameterValue',
        data: {parameter, value}
    });
}

function createInitialValuesEvent(parameterValues) {
    return JSON.stringify({
        'event': 'initialValues',
        data: {parameterValues}
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

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
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

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
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

            assert.deepEqual(store.state.scriptConfig.parameters, expectedParameters);
        });

        it('Test remove parameter', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            sendEventFromServer(createConfigEvent(config));

            sendEventFromServer(createRemoveParameterEvent(config.parameters[0].name));

            config.parameters.splice(0, 1);

            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });
    });

    describe('Test reconnection', function () {
        it('Test disconnect before initial config', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];
            sendSocketError(new SocketClosedError());

            assert.isNull(store.state.scriptConfig.scriptConfig);
            assert.equal(store.state.scriptConfig.loadError, 'Failed to connect to the server');
        });

        it('Test disconnect after initial config', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await this.disconnectSocket(50);

            const newObserver = observers[0];

            assert.notEqual(newObserver, oldObserver);
            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.isNull(store.state.scriptConfig.loadError);
        });

        it('Test reload config after reconnect', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();
            sendEventFromServer(createConfigEvent(config));

            await this.disconnectSocket(50);

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            config.name = 'new name';
            config.parameters.push({'name': 'param3'});

            sendEventFromServer(createConfigEvent(config));

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });
    });

    describe('Test send current value', function () {
        it('Test send value', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [createSentValueEvent('param1', 123)]);
        });

        it('Test send same value multiple times', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [createSentValueEvent('param1', 123)]);
        });

        it('Test send same parameter different values', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 456});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [
                createSentValueEvent('param1', 123),
                createSentValueEvent('param1', 456),
                createSentValueEvent('param1', 123)
            ]);
        });

        it('Test send different parameters', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param2', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 'hello'});

            assert.deepEqual(this.sentData, [
                createSentValueEvent('param2', 123),
                createSentValueEvent('param1', 'hello')
            ]);
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

            assert.deepEqual(this.sentData, [
                createSentValueEvent('param2', 123),
                createSentValueEvent('param1', 'hello')
            ]);
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
});