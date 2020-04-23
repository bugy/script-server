import {clearArray, removeElement, SocketClosedError} from '@/common/utils/common';
import scriptConfig, {__RewireAPI__ as SocketRewireAPI} from '@/main-app/store/scriptConfig';
import {createLocalVue} from '@vue/test-utils';
import {assert} from 'chai';
import Vuex from 'vuex';
import {timeout} from './test_utils'


const localVue = createLocalVue();
localVue.use(Vuex);

function createStore() {
    return new Vuex.Store({
        modules: {
            scriptConfig: scriptConfig
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
        name: 'testScript',
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

function createSentValue(parameter, value) {
    return JSON.stringify({
        'event': 'parameterValue',
        data: {parameter, value}
    });
}

describe('Test scriptConfig module', function () {
    let observers = [];

    beforeEach(function () {
        const sentData = [];

        this.sentData = sentData;

        SocketRewireAPI.__Rewire__('ReactiveWebSocket', function (path, observer) {
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
            observer.onError(new SocketClosedError());
            await timeout(awaitTimeout);
        };
    });

    describe('Test config in single connection', function () {
        it('Test connect on reload', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            observers[0].onNext(createConfigEvent(config));

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });

        it('Test replace config', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            observers[0].onNext(createConfigEvent(config));

            config.name = 'new name';
            config.parameters.splice(1, 1);
            config.parameters.push({name: 'param3'});

            observers[0].onNext(createConfigEvent(config));

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });

        it('Test add parameter', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            observers[0].onNext(createConfigEvent(config));

            const newParameter = {name: 'param3', type: 'multiselect', 'default': 'abc'};

            observers[0].onNext(createAddParameterEvent(newParameter));

            const expectedParameters = config.parameters.concat([newParameter]);
            newParameter.multiselect = true;

            assert.deepEqual(store.state.scriptConfig.parameters, expectedParameters);
        });

        it('Test remove parameter', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();

            observers[0].onNext(createConfigEvent(config));

            observers[0].onNext(createRemoveParameterEvent(config.parameters[0].name));

            config.parameters.splice(0, 1);

            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });
    });

    describe('Test reconnection', function () {
        it('Test disconnect before initial config', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];
            oldObserver.onError(new SocketClosedError());

            assert.isNull(store.state.scriptConfig.scriptConfig);
            assert.equal(store.state.scriptConfig.loadError, 'Failed to connect to the server');
        });

        it('Test disconnect after initial config', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const oldObserver = observers[0];

            const config = createConfig();
            oldObserver.onNext(createConfigEvent(config));

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
            observers[0].onNext(createConfigEvent(config));

            await this.disconnectSocket(50);

            const newObserver = observers[0];

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            config.name = 'new name';
            config.parameters.push({'name': 'param3'});

            newObserver.onNext(createConfigEvent(config));

            assert.deepEqual(store.state.scriptConfig.scriptConfig, config);
            assert.deepEqual(store.state.scriptConfig.parameters, config.parameters);
        });
    });

    describe('Test send current value', function () {
        it('Test send value', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [createSentValue('param1', 123)]);
        });

        it('Test send same value multiple times', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [createSentValue('param1', 123)]);
        });

        it('Test send same parameter different values', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 456});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 123});

            assert.deepEqual(this.sentData, [
                createSentValue('param1', 123),
                createSentValue('param1', 456),
                createSentValue('param1', 123)
            ]);
        });

        it('Test send different parameters', function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param2', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 'hello'});

            assert.deepEqual(this.sentData, [
                createSentValue('param2', 123),
                createSentValue('param1', 'hello')
            ]);
        });

        it('Test resend values on reconnect', async function () {
            const store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});

            const config = createConfig();
            observers[0].onNext(createConfigEvent(config));

            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param2', value: 123});
            store.dispatch('scriptConfig/sendParameterValue', {parameterName: 'param1', value: 'hello'});

            clearArray(this.sentData);

            await this.disconnectSocket(100);
            assert.deepEqual(this.sentData, []);

            observers[0].onNext(createConfigEvent(config));

            assert.deepEqual(this.sentData, [
                createSentValue('param2', 123),
                createSentValue('param1', 'hello')
            ]);
        });
    });

    describe('Test force allowed values', function () {
        let store;

        beforeEach(function () {
            store = createStore();
            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'my script'});
        });

        const assertAllowedValues = (parameterName, expectedValues) => {
            const param = store.state.scriptConfig.parameters.find(p => p.name === parameterName);
            assert.exists(param, 'Couldn\'t find parameter for name: ' + parameterName);

            assert.deepEqual(param.values, expectedValues);
        };

        const setForcedAllowedValues = (values) => {
            store.dispatch('scriptConfig/setForcedAllowedValues', values);
        };

        const sendConfig = () => {
            const config = createConfig();
            observers[0].onNext(createConfigEvent(config));
        };

        it('Test force before initial config', function () {
            setForcedAllowedValues({'param2': '12345'});

            sendConfig();

            assertAllowedValues('param2', DEFAULT_PARAM2_VALUES.concat(['12345']));
        });

        it('Test force after initial config', function () {
            sendConfig();

            setForcedAllowedValues({'param2': '12345'});

            assertAllowedValues('param2', DEFAULT_PARAM2_VALUES.concat(['12345']));
        });

        it('Test force for added parameter', function () {
            setForcedAllowedValues({'param3': '12345'});

            sendConfig();

            const newParameter = {name: 'param3', type: 'list', values: ['hello', 'world']};
            observers[0].onNext(createAddParameterEvent(newParameter));

            assertAllowedValues('param3', ['hello', 'world', '12345']);
        });

        it('Test force for updated parameter', function () {
            setForcedAllowedValues({'param2': '12345'});

            sendConfig();

            const newParameterConfig = {name: 'param2', type: 'list', values: ['999']};
            observers[0].onNext(createUpdateParameterEvent(newParameterConfig));

            assertAllowedValues('param2', ['999', '12345']);
        });

        it('Test force when initial values undefined', function () {
            setForcedAllowedValues({'param3': '12345'});

            const config = createConfig();
            config.parameters.push({name: 'param3', type: 'list'});
            observers[0].onNext(createConfigEvent(config));

            assertAllowedValues('param3', ['12345']);
        });

        it('Test force when multiselect', function () {
            setForcedAllowedValues({'param3': ['v2', 'v4', 'v6']});

            const config = createConfig();
            config.parameters.push({name: 'param3', type: 'multiselect', values: ['v1', 'v2', 'v3']});
            observers[0].onNext(createConfigEvent(config));

            assertAllowedValues('param3', ['v1', 'v2', 'v3', 'v4', 'v6']);
        });

        it('Test force when server_file', function () {
            setForcedAllowedValues({'param3': 'my.dat'});

            const config = createConfig();
            config.parameters.push({name: 'param3', type: 'server_file', values: ['log.txt', 'admin.pwd']});
            observers[0].onNext(createConfigEvent(config));

            assertAllowedValues('param3', ['log.txt', 'admin.pwd', 'my.dat']);
        });

        it('Test force when server_file recursive ', function () {
            setForcedAllowedValues({'param3': 'my.dat'});

            const config = createConfig();
            config.parameters.push({
                name: 'param3',
                type: 'server_file',
                values: ['log.txt', 'admin.pwd'],
                fileRecursive: true
            });
            observers[0].onNext(createConfigEvent(config));

            assertAllowedValues('param3', ['log.txt', 'admin.pwd']);
        });

        it('Test force when null value', function () {
            setForcedAllowedValues({'param2': null});

            sendConfig();

            assertAllowedValues('param2', DEFAULT_PARAM2_VALUES);
        });

        it('Test force after reset', function () {
            setForcedAllowedValues({'param2': 'new value'});

            store.dispatch('scriptConfig/reloadScript', {selectedScript: 'another script'});

            sendConfig();

            assertAllowedValues('param2', DEFAULT_PARAM2_VALUES);
        });

    });
});